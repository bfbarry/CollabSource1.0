import base64
import os
from datetime import datetime, timedelta
from time import time
from flask import current_app, url_for
from flask_login import UserMixin, AnonymousUserMixin # incorporates requirements for flask-login
from werkzeug.security import generate_password_hash, check_password_hash
from dataclasses import dataclass
#avatar imports
from hashlib import md5
from app import db, login
from app.search import add_to_index, remove_from_index, query_index

class SearchableMixin(object):
    """
    Used by Project() to search
    from https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvi-full-text-search
    """
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = [] # named after associated SQL statement see https://stackoverflow.com/questions/6332043/sql-order-by-multiple-values-in-specific-order/6332081#6332081
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by( 
            db.case(when, value=cls.id)), total #case statement ensures results are in same order as IDs

    @classmethod
    def before_commit(cls, session):
        '''keeps track of old model formats/IDs before commit'''
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj, stage='update') # this is when tags are added
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        '''refreshes an index'''
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj,stage='reindex')

class PaginatedAPIMixin:
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page=page, per_page=per_page, error_out=False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data

class TagMixin:
    """Used by User and Project"""  
    # def __init__(self, **kwargs):
    #     super(TagMixin, self).__init__(**kwargs)
    #     self.tag_list = [tag.name for tag in self.tags]

    def add_tags(self, _tags, kind='tags'):
        '''where _tags is list of tag objs fed in route'''
        for tag in _tags:
            if not self.has_tag(tag, kind):
                getattr(self,kind).append(tag)

    def rm_tag(self, tag, kind='tags'):
        if self.has_tag(tag):
            getattr(self,kind).remove(tag)
        
    def has_tag(self, tag, kind='tags'):
        if kind in ['tags', 'interests']:
            return self.tags.filter(
                project_tag_map.c.tag_id == tag.id).count() > 0 # checking if 1 or 0
        else:
            return self.wanted_positions.filter(
                position_map.c.position_id == tag.id).count() > 0

    def tag_update(self, TagModel, kind, input_tags):
        """TagModel: Tag or Position
        self: instance of Project or User
        input_tags: list of str tags
        follow call with db.session.commit()"""
        # TODO: remove kind and only rely on TagModel
        if kind=='tags':
            orig_tags = [t.name for t in self.tags]
        elif kind=='wanted_positions':
            orig_tags = [t.name for t in self.wanted_positions]
        tag_names = [t.name for t in TagModel.query.all()]
        tagms = [] #models to add to Project or User
        for t in orig_tags: # removing tags
            if t not in input_tags:
                self.rm_tag(TagModel.query.filter_by(name=t).first(), kind=kind)
        for tag in input_tags:
            tag = tag.lower()
            if tag not in tag_names: # creating new tag models if they don't already exist
                db.session.add(TagModel(name=tag))
                db.session.commit() #redundant?
            tagms.append(TagModel.query.filter_by(name=tag).first())
            
        self.add_tags(tagms,kind=kind)

# set up the event handlers
db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

## Association tables ##

followers = db.Table('followers',
            db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
            db.Column('followed_id', db.Integer, db.ForeignKey('user.id')) )

# project tags
project_creator_map = db.Table('project_creator_map', 
                db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
                db.Column('user_id', db.Integer, db.ForeignKey('user.id')) )

project_tag_map = db.Table('project_tag_map', 
                db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
                db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')) )

# user interests
user_tag_map = db.Table('user_tag_map', 
                db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')) )

resource_tag_map = db.Table('resource_tag_map', 
                db.Column('resource_id', db.Integer, db.ForeignKey('resource.id')),
                db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')) )

    # for Projects' wanted positions
position_map = db.Table('position_map', 
                db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
                db.Column('position_id', db.Integer, db.ForeignKey('position.id')) )

## for starring projects
# project_followers = db.Table('members',
#     db.Column('proj_follower_id', db.Integer, db.ForeignKey('user.id')),
#     db.Column('proj_followed_id', db.Integer, db.ForeignKey('project.id'))
# )

class JoinRequest(db.Model, PaginatedAPIMixin):
    """
    Association table User <--> Project 
    kind: 'invite' (project admin-->user) or 'request' (user-->project)
    status: 'pending', 'accepted', 'rejected' 
    """
    __tablename__ = 'join_requests'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True) 
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    
    user = db.relationship('User', back_populates='proj_requests')
    project = db.relationship('Project', back_populates='user_requests')
    kind = db.Column(db.String(15))
    msg = db.Column(db.String(650))
    status = db.Column(db.String(15))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) #indexed to order them easily

    def to_dict(self): #for invitation endpoint
        data = {'user_id': self.user_id,
                'project_id':self.project_id,
                'username': self.user.username,
                'projectname': self.project.name,
                'msg':self.msg,
                'kind':self.kind,
                'members': [u.user_id for u in Project.query.get(self.project_id).members],
                'timestamp':self.timestamp.isoformat() + 'Z'}
        return data

class ProjMember(db.Model):
    '''
    '''
    __tablename__ = 'proj_members'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True) 
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    rank_id = db.Column(db.Integer, db.ForeignKey('rank.id')) # primary_key=True?
    position_id = db.Column(db.Integer, db.ForeignKey('position.id')) # primary_key=True?
    
    user = db.relationship('User', back_populates='member_of')
    project = db.relationship('Project', back_populates='members')
    rank = db.relationship('Rank', back_populates='member_ranks')
    position = db.relationship('Position', back_populates='member_positions')
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(ProjMember, self).__init__(**kwargs)
        proj = Project.query.get(self.project_id)
        u = User.query.get(self.user_id)

        if self.rank_id is None:
            
            if u == proj.creator:
                self.rank = Rank.query.filter_by(name='Admin').first()
            if self.rank is None:
                self.rank = Rank.query.filter_by(default=True).first()

# class UserProjRecommendation(db.Model):
#     """Recommend projects to user and vice versa"""
#     __tablename__ = 'user_proj_recommendations'
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
#     project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
#     rank = db.Column(db.Integer)

#     user = db.relationship('User', back_populates='recommendations')
#     project = db.relationship('Project', back_populates='recommendations')

class ScrumTask(db.Model):
    __tablename__ = 'scrum_tasks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    task_type = db.Column(db.String(15))
    text = db.Column(db.String(650))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) #indexed to order them easily

    project = db.relationship('Project', back_populates='scrum_board')

    def __repr__(self):
        return f'<{self.task_type}: {self.text} by {self.user_id} proj {self.project_id}>'

class User(TagMixin, PaginatedAPIMixin, UserMixin, db.Model):
    """ 
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # From the perspective of the follower
    followed = db.relationship( # Looking at relationship from follower (one) --> following (many), this yield the right side (those followed)
        'User', secondary=followers, #Self-ref, association table
        primaryjoin=(followers.c.follower_id == id), #condition to join left side (follower) w/ assoc. table
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic') #defines how this relationship will be accessed from the right side entity

    proj_requests = db.relationship('JoinRequest', back_populates='user', 
                        lazy='dynamic',cascade="all, delete-orphan") # cascade used to remove
    last_notif_read_time = db.Column(db.DateTime)
    tags = db.relationship(  #i.e., interests
        'Tag', secondary=user_tag_map, 
        backref=db.backref('user_tag_map', lazy='dynamic'), lazy='dynamic') 
    member_of = db.relationship('ProjMember',back_populates='user',
                        lazy='dynamic',cascade="all, delete-orphan")  

    # recommendations = db.relationship('UserProjRecommendation', back_populates='user',
    #                                     lazy='dynamic',cascade='all, delete-orphan')

    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None: # lint error because backrefd
            if self.email in current_app.config['ADMINS']:
                self.role = Role.query.filter_by(name='Admin').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
    
    ### API ###
    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.isoformat() + 'Z',
            'about_me': self.about_me,
            'project_count': self.member_of.count(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                # 'projects': url_for('api.get_projects', q=None), #q has to be query instance
                'followers': url_for('api.get_followers', id=self.id),
                'followed': url_for('api.get_followers', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email: #only when users request their own data
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60): # if at least 60 seconds left on current toekn
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        '''makes currently assigned token invalid'''
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user

    ### REQUEST FUNC ###
    def new_requests(self):
        '''Counts new requests
            notif if:
            a join request is sent to their project,
            an invitation is received by self
        '''
        last_read_time = self.last_notif_read_time or datetime(1900,1,1)
        return JoinRequest.query.filter_by(kind='request').join(ProjMember,
            (JoinRequest.project_id == ProjMember.project_id)).filter(
                ProjMember.user_id == self.id).filter(JoinRequest.timestamp > last_read_time).count() + \
            JoinRequest.query.filter_by(user_id = self.id, kind='invite').filter(
                        JoinRequest.timestamp > last_read_time).count()

    def send_request(self,proj,r,kind='request',u_inv=None):
        ''' to send request to join proj, or invite '''
        if kind == 'request':
            if self.can_request(proj):
                self.proj_requests.append(r)
        elif kind == 'invite':
            if u_inv.can_request(proj):
                u_inv.proj_requests.append(r)

    def cancel_request(self,proj,r,kind='request',u_inv=None):
        ''' should make this easier where r not required '''
        if kind == 'request':
            if not self.can_request(proj):
                self.proj_requests.remove(r)
        elif kind == 'invite':
            if u_inv.can_request(proj):
                u_inv.proj_requests.remove(r)

    def can_request(self, proj):
        ''' if sent a request or (maybe?) if member'''
        # if self.is_member(proj):
        #     return False
        num_requests = self.proj_requests.filter(
            JoinRequest.__table__.c.project_id == proj.id).count()
        num_memberships = self.member_of.filter(
            ProjMember.__table__.c.project_id == proj.id).count()
        return not num_requests + num_memberships > 0
    
    ### user-user func ###
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0 # checking if 1 or 0
    
    def followed_projects(self):
        """ Displays projects of people User follows
        Need to figure out where to put the stream of posts (as this is more of a secondary feature) """
        return Project.query.join(
            followers, (followers.c.followed_id == Project.user_id)).filter( #post ID and followed_id match
                followers.c.follower_id == self.id).order_by(
                    Project.timestamp.desc())

    ### PERMISSION FUNCS (both site-wide and project scope)###
    def can(self,perm,proj=None):
        ''' check permissions for site or given proj '''
        if proj:
            membership = self.member_of.filter(ProjMember.__table__.c.project_id == proj.id).first()
            return membership.rank is not None and membership.rank.has_permission(perm)
        else: #site case
            return self.role is not None and self.role.has_permission(perm)

    def is_admin(self,proj=None):
        if proj:
            return self.can(ProjPerm.ADMIN, proj)
        else: #site case
            return self.can(SitePerm.ADMIN)

    ### member functions IN PROGRESS ###
    def star(self, proj):
        """Star project User is interested in. Need following project association table"""
        return
    
    ### PASSWORD FUNC ###
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def __repr__(self):
        return '<User {}>'.format(self.username)   

class AnonymousUser(AnonymousUserMixin):
    def can(self,permissions):
        return False
    def is_admin(self):
        return False

@login.user_loader
def load_user(id):
    """
    User loader function: loads a user given the ID
    Helps Flask-Login load a user. 
    """
    return User.query.get(int(id))

class SitePerm:
    '''TODO Permissions for website roles
    Subject to change'''
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16

class ProjPerm:
   '''TODO Permissions for project ranks'''
   READ = 1
   MODERATE = 2
   ADMIN = 4

class Role(db.Model):
    ''' TODO Role for user across the website'''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25),unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0
    
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm
    
    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm
    
    def reset_permissions(self):
        self.permissions = 0
    
    def has_permission(self, perm):
        return self.permissions & perm == perm

    @staticmethod # because it makes sense to put in this class
    def insert_roles():
        roles = {
                'User': [SitePerm.FOLLOW, SitePerm.COMMENT, SitePerm.WRITE],
                'Moderator': [SitePerm.FOLLOW, SitePerm.COMMENT,
                                SitePerm.WRITE, SitePerm.MODERATE],
                'Admin': [SitePerm.FOLLOW, SitePerm.COMMENT,
                                SitePerm.WRITE, SitePerm.MODERATE,
                                SitePerm.ADMIN]
                }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<{}>'.format(self.name)

class Tag(SearchableMixin, db.Model):
    __searchable__ = ['name']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    
    #project tags
    tags = db.relationship(
        'Project', secondary=project_tag_map,
        backref=db.backref('project_tag_map', lazy='dynamic'), lazy='dynamic') 
    
    def __repr__(self):
        return '<{}>'.format(self.name)

class Position(SearchableMixin, db.Model):
    """Both for 'wanted positions' and member descriptors """
    __searchable__ = ['name']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), unique=True)
    
    wanted_positions = db.relationship( 
        'Project', secondary=position_map,
        backref=db.backref('position_map', lazy='dynamic'), lazy='dynamic')

    member_positions = db.relationship('ProjMember',back_populates='position',
                        lazy='dynamic',cascade="all, delete-orphan")   
    
    def __repr__(self):
        return '<{}>'.format(self.name)

class Project(db.Model, TagMixin, PaginatedAPIMixin, SearchableMixin):
    """tags and wanted positions share the same methods due to overlap in functionality
    team_size: range (5-10, 25-40 etc) """
    __searchable__ = ['category','name','descr', 'tags'] #  needs 'wanted_positions' 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    category = db.Column(db.String(60))
    descr = db.Column(db.String(140))
    skill_level = db.Column(db.String(20))
    setting = db.Column(db.String(20))
    team_size = db.Column(db.String(20))
    # location = db.Column(db.String(20))
    chat_link = db.Column(db.String(512)) # Discord, slack etc.
    # non optional variables
    language = db.Column(db.String(5))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) # index to retrieve projs in chron. order
    #! removed user_id

    __mapper_args__ = {'polymorphic_on': category}

    creators = db.relationship('User', secondary=project_creator_map, 
        backref=db.backref('project_creator_map', lazy='dynamic'), lazy='dynamic') 

    tags = db.relationship( # Looking at relationship from project (one) --> tags (many)
        'Tag', secondary=project_tag_map, #Self-ref, association table
        # primaryjoin=(project_tag_map.c.project_id == id), 
        # secondaryjoin=(project_tag_map.c.tag_id == project_tag_map.tag_id),
        backref=db.backref('project_tag_map', lazy='dynamic'), lazy='dynamic') #defines how this relationship will be accessed from the right side entity

    wanted_positions = db.relationship( # represented by 'wanted_positions' for kind arg in tag functions
        'Position', secondary=position_map, 
        backref=db.backref('position_map', lazy='dynamic'), lazy='dynamic') 
        
    user_requests = db.relationship('JoinRequest', back_populates='project',cascade="all, delete-orphan", lazy='dynamic') # try setting to __tablename__ 

    members = db.relationship('ProjMember',back_populates='project',
                        lazy='dynamic',cascade="all, delete-orphan")
    
    # recommendations = db.relationship('UserProjRecommendation', back_populates='project',
    #                                     lazy='dynamic',cascade='all, delete-orphan')

    scrum_board = db.relationship('ScrumTask', back_populates='project',cascade="all, delete-orphan", lazy='dynamic') # try setting to __tablename__ 
    ### API ###
    def to_dict_main(self): #inherited classes will have to_dict()
        data = {
            'id': self.id,
            'name': self.name,
            'creators': [{'id':u.id,'name':u.username} for u in self.creators],
            'category': self.category,
            'timestamp': self.timestamp.isoformat() + 'Z',
            'descr': self.descr,
            'skill_level': self.skill_level,
            'setting': self.setting,
            'members': {u.user_id : {'rank':u.rank.name, 'position':u.position.name if u.position is not None else None} for u in self.members}, #Make name None default and remove the None check once 
            'requests': {r.user_id: {'kind':r.kind, 'msg':r.msg, 'timestamp':r.timestamp.isoformat() + 'Z'} if len(list(self.user_requests)) > 0 else None for r in self.user_requests},
            'tags' : [t.name for t in self.tags], 
            'wanted_positions' : [p.name for p in self.wanted_positions],
            'language': self.language,
            '_links': {
                'self': url_for('api.get_project', id=self.id),
                # 'followers': url_for('api.get_followers', id=self.id),
                'chat_link': self.chat_link
            }
        }
        return data
    
    tag_model_map={'tags':Tag, 'wanted_positions':Position}
    def from_dict_main(self, data):
        for field in ['name','category','descr','skill_level','setting','chat_link','tags','wanted_positions','creators']:
            if field in data:
                if field in ['tags','wanted_positions']:
                    continue
                    self.tag_update(self.tag_model_map[field], field, data[field])
                if field == 'creators':
                    for c_id in data[field]:
                       self.creators.append(User.query.get(c_id))
                else:
                    setattr(self, field, data[field])
    
    def scrum_to_dict(self):
        data = {
            'Requested' : [],
            'To Do' : [],
            'In Progress' : [],
            'Done' : []
        }
        for task in self.scrum_board.all():
            data[task.task_type].append({'user_id': task.user_id, 'text':task.text, 'timestamp': task.timestamp.isoformat() + 'Z'})

        return data

    ### REQUEST FUNC ###
    def add_member(self,user_id,membership):
        if not self.is_member(user_id):
            self.members.append(membership)

    def remove_member(self, user_id):
        if self.is_member(user_id):
            membership = self.members.filter_by(user_id=user_id)
            self.members.remove(membership)

    def is_member(self,user_id):
        return self.members.filter(
            ProjMember.__table__.c.user_id == user_id).count() > 0 # checking if 1 or 0

    def __repr__(self):
        return '<Project {}>'.format(self.name)

class Rank(db.Model):
    ''' Rank for member (user) within a project
    Same factory pattern as Role '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25),unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    member_ranks = db.relationship('ProjMember', back_populates='rank', lazy='dynamic') # ,cascade="all, delete-orphan"
    def __init__(self, **kwargs):
        super(Rank, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0
    
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm
    
    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm
    
    def reset_permissions(self):
        self.permissions = 0
    
    def has_permission(self, perm):
        return self.permissions & perm == perm

    @staticmethod # because it makes sense to put in this class
    def insert_ranks():
        ranks = {'Member':[ProjPerm.READ],
                'Moderator':[ProjPerm.READ, ProjPerm.MODERATE],
                'Admin':[ProjPerm.READ, ProjPerm.MODERATE, ProjPerm.ADMIN]}
        default_rank = 'Member'
        for r in ranks:
            rank = Rank.query.filter_by(name=r).first()
            if rank is None:
                rank = Rank(name=r)
            rank.reset_permissions()
            for perm in ranks[r]:
                rank.add_permission(perm)
            rank.default = (rank.name == default_rank)
            db.session.add(rank)
        db.session.commit()

    def __repr__(self):
        return '<{}>'.format(self.name)

class Learning(Project):
    '''Can be study group for a course, or just auto-didacts studying a subject together
    pace: according to perosnal timelines or college terms
    learning_category: general subject matter (e.g. Math) '''
    
    __mapper_args__ = {'polymorphic_identity': 'learning'}
    id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    
    ### Project spec properties ###
    pace = db.Column(db.String(60))    
    learning_category = db.Column(db.String(60))
    subject = db.Column(db.String(60)) # may be redundant with project name
    resource = db.Column(db.String(70)) #can be textbook, playlist, etc. Not same as Resource class

    ### API ###
    def to_dict(self):
        main_data = self.to_dict_main()
        data = {
            'pace': self.pace,
            'learning_category': self.learning_category,
            'subject': self.subject,
            'resource': self.resource,
        }

        return {**main_data, **data}

    def from_dict(self, data):
        self.from_dict_main(data)
        for field in ['pace','learning_category','subject','resource']:
            if field in data:
                setattr(self, field, data[field])

    # crude way to add new subjects to learning_categories
    # if subject.lower() not in [i for row in self.learning_categories.values() for i in row]: # <-- list of all subjects
    #     ProjectDataBase.learning_categories[learning_category].append(subject)

class SoftwareDev(Project):
    """Software Development project
    kind: Web Development, Mobile App
    Programming language will be a Tag for now"""
    __mapper_args__ = {'polymorphic_identity': 'software_development'}
    id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    
    ### Project spec properties ###
    sub_category = db.Column(db.String(60))    

    ### API ###
    def to_dict(self):
        main_data = self.to_dict_main()
        data = {'sub_category': self.sub_category}
        return {**main_data, **data}

    def from_dict(self, data):
        self.from_dict_main(data)
        for field in ['sub_category']:
            if field in data:
                setattr(self, field, data[field])

class Engineering(Project):
    """[Physical] engineering project
    """
    __mapper_args__ = {'polymorphic_identity': 'engineering'}
    id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    
    ### Project spec properties ###
    sub_category = db.Column(db.String(60))    

    ### API ###
    def to_dict(self):
        main_data = self.to_dict_main()
        data = {'sub_category': self.sub_category}
        return {**main_data, **data}

    def from_dict(self, data):
        self.from_dict_main(data)
        for field in ['sub_category']:
            if field in data:
                setattr(self, field, data[field])

class DataScience(Project):
    """Data Science/Machine Learning project
    """
    __mapper_args__ = {'polymorphic_identity': 'data_science'}
    id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    
    ### Project spec properties ###
    sub_category = db.Column(db.String(60))    

    ### API ###
    def to_dict(self):
        main_data = self.to_dict_main()
        data = {'sub_category': self.sub_category}
        return {**main_data, **data}

    def from_dict(self, data):
        self.from_dict_main(data)
        for field in ['sub_category']:
            if field in data:
                setattr(self, field, data[field])

class Business(Project):
    """Broader category
    """
    __mapper_args__ = {'polymorphic_identity': 'business'}
    id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    
    ### Project spec properties ###
    sub_category = db.Column(db.String(60))    

    ### API ###
    def to_dict(self):
        main_data = self.to_dict_main()
        data = {'sub_category': self.sub_category}
        return {**main_data, **data}

    def from_dict(self, data):
        self.from_dict_main(data)
        for field in ['sub_category']:
            if field in data:
                setattr(self, field, data[field])

class Research(Project):
    """Research Project
    field: academic field
    """
    __mapper_args__ = {'polymorphic_identity': 'research'}
    id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    
    ### Project spec properties ###
    field = db.Column(db.String(60))    

    ### API ###
    def to_dict(self):
        main_data = self.to_dict_main()
        data = {'field': self.field}
        return {**main_data, **data}

    def from_dict(self, data):
        self.from_dict_main(data)
        for field in ['field']:
            if field in data:
                setattr(self, field, data[field])

class Community(Project):
    """E.g. trash clean up etc.
    """
    __mapper_args__ = {'polymorphic_identity': 'community'}
    id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    
    ### Project spec properties ###
    sub_category = db.Column(db.String(60))    

    ### API ###
    def to_dict(self):
        main_data = self.to_dict_main()
        data = {'sub_category': self.sub_category}
        return {**main_data, **data}

    def from_dict(self, data):
        self.from_dict_main(data)
        for field in ['sub_category']:
            if field in data:
                setattr(self, field, data[field])

class Entertainment(Project):
    """E.g. YouTube collabs etc
    """
    __mapper_args__ = {'polymorphic_identity': 'entertainment'}
    id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    
    ### Project spec properties ###
    sub_category = db.Column(db.String(60))    

    ### API ###
    def to_dict(self):
        main_data = self.to_dict_main()
        data = {'sub_category': self.sub_category}
        return {**main_data, **data}

    def from_dict(self, data):
        self.from_dict_main(data)
        for field in ['sub_category']:
            if field in data:
                setattr(self, field, data[field])

## KEEP THIS AFTER ALL PROJECT CLASSES
# imported in main/routes.py to instatiate specific project classes in /create_project
SUB_PROJS = (Learning, SoftwareDev, Engineering, DataScience, Business, Research, Community, Entertainment)
PROJ_CATEGORIES = {' '.join(table.__mapper_args__['polymorphic_identity'].split('_')):table \
                        for table in SUB_PROJS} # 
# PROJ_CATEGORIES = {cl.field_name:cl for cl in (Learning, SoftwareDev, Engineering)}

# imported in main/forms.py for SelectField options
PROJ_CAT_KEYS = tuple(PROJ_CATEGORIES.keys())

class Resource(TagMixin, db.Model, PaginatedAPIMixin):
    __searchable__ = ['category','name','descr', 'tags'] #  needs 'wanted_positions' 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    category = db.Column(db.String(60)) # could be multiple!
    descr = db.Column(db.String(140))
    link = db.Column(db.String(512)) # Discord, slack etc.
    # non optional variables
    language = db.Column(db.String(5))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) # index to retrieve projs in chron. order
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
    accepted = db.Column(db.Boolean, default=False) # False if user submitted one pending review 

    tags = db.relationship( # Looking at relationship from project (one) --> tags (many)
        'Tag', secondary=resource_tag_map, #Self-ref, association table
        backref=db.backref('resource_tag_map', lazy='dynamic'), lazy='dynamic') #defines how this relationship will be accessed from the right side entity

    ### API ###
    def to_dict(self): #inherited classes will have to_dict()
        data = {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'descr': self.descr,
            'link': self.link,
            'tags' : [t.name for t in self.tags] 
        }
        return data
    
    def from_dict(self, data):
        for field in ['name','category','descr','link','user_id','accepted']:
            if field in data:
                setattr(self, field, data[field])

    def __repr__(self):
        return '<Project {}>'.format(self.name)