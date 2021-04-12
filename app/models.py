from datetime import datetime
from time import time
from flask import current_app
from flask_login import UserMixin # incorporates 4 requirements for flask-login
from werkzeug.security import generate_password_hash, check_password_hash
#avatar imports
from hashlib import md5
import jwt
from app import db, login
from app.search import add_to_index, remove_from_index, query_index

class SearchableMixin(object):
    """Used by Project() to search"""
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
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        '''refreshes an index'''
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

## Association tables ##

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

# members = db.Table('members',
#     db.Column('member_id', db.Integer, db.ForeignKey('user.id')),
#     db.Column('member_of_id', db.Integer, db.ForeignKey('project.id'))
# )

## for starring projects
# project_followers = db.Table('members',
#     db.Column('proj_follower_id', db.Integer, db.ForeignKey('user.id')),
#     db.Column('proj_followed_id', db.Integer, db.ForeignKey('project.id'))
# )

class User(UserMixin, db.Model):
    """ 
    $ flask db migrate -m "users table" 
    $ flask db upgrade
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    projects = db.relationship('Project', backref='creator', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # From the perspective of the follower
    followed = db.relationship( # Looking at relationship from follower (one) --> following (many), this yield the right side (those followed)
        'User', secondary=followers, #Self-ref, association table
        primaryjoin=(followers.c.follower_id == id), #condition to join left side (follower) w/ assoc. table
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic') #defines how this relationship will be accessed from the right side entity
        
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
    
    ### member functions IN PROGRESS ###
    def star(self, proj):
        """Star project User is interested in. Need following project association table"""
        return

    def request_join(self, proj):
        """Request to join a project"""
        return
        if not self.is_member(proj):
            # project_requests not yet defined
            self.project_requests.append(proj)
    
    def is_member(self, proj):
        return
        return self.followed.filter(
            members.c.member_of_id == proj.id).count() > 0

    ### PASSWORD FUNC ###
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        """expires_in: seconds"""
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def __repr__(self):
        return '<User {}>'.format(self.username)   

@login.user_loader
def load_user(id):
    """
    User loader function: loads a user given the ID
    Helps Flask-Login load a user. 
    """
    return User.query.get(int(id))

class Project(SearchableMixin, db.Model):
    __searchable__ = ['category','name','descr'] # subject to change
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(60))
    name = db.Column(db.String(60))
    descr = db.Column(db.String(140))
    skill_level = db.Column(db.String(20))
    setting = db.Column(db.String(20))
    #location = db.Column(db.String(20))
    # non optional variables
    language = db.Column(db.String(5))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) #creator ID (want this to be many to one: many creator to one proj)
    
    __mapper_args__ = {'polymorphic_on': category}
    # member_of = db.relationship( #also need a relationship in User()?
    #     'User', secondary=members,
    #     primaryjoin=(members.c.member_id == id),
    #     secondaryjoin=(members.c.member_of_id == id),
    #     backref=db.backref('members', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<Project {}>'.format(self.name)
        
class Learning(Project):
    '''Can be study group for a course, or just auto-didacts studying a subject together
    pace: according to perosnal timelines or college terms
    learning_category: general subject matter (e.g. Math) '''
    
    __mapper_args__ = {'polymorphic_identity': 'learning'}
    id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    field_name = 'learning' #SelectField option in form
    
    ### Project spec properties ###
    pace = db.Column(db.String(60))    
    learning_category = db.Column(db.String(60))
    subject = db.Column(db.String(60)) #still have to figure out how to implement this
    resource = db.Column(db.String(70)) #can be textbook, playlist, etc.

    # crude way to add new subjects to learning_categories
    # if subject.lower() not in [i for row in self.learning_categories.values() for i in row]: # <-- list of all subjects
    #     ProjectDataBase.learning_categories[learning_category].append(subject)


## KEEP THIS AFTER ALL PROJECT CLASSES
# imported in main/routes.py to instatiate specific project classes in /create_project
proj_categories = {'learning': Learning} #, 'software development':SoftwareDev} 
# proj_categories = {cl.field_name:cl for cl in (Learning, SoftwareDev)}
# imported in main/forms.py for SelectField options
proj_cat_keys = tuple(proj_categories.keys())