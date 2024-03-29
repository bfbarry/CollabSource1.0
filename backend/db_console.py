'''
Script to modify database
'''
from datetime import datetime
from app import create_app, db
from app.models import ScrumTask, User, Role, Project, Position, JoinRequest, ProjMember, Tag, ProjPerm,\
                            Learning, SoftwareDev, Resource
from app.utils import api_func
app = create_app()
app.app_context().push() # to accomodate updated app structure

''' 
    ! COMMON COMMANDS !
#Querying
[Model].query.filter_by(attr=...).first_or_404() # or just .first()

#Session
db.session.add(instance)
db.session.commit()
db.session.delete()

instead of paginate, use .all() at end of query

"in" aggregator : Project.query.filter(Project.id.in_( ids)).all()
'''
def add_proj(name, proj_model,skill_level,setting,descr, language, chat_link, tags, proj_kwargs):
    project = proj_model()
    project.from_dict({'name' : name, 'category' : proj_model.__mapper_args__['polymorphic_identity'], 
                            'skill_level' : skill_level, 'setting' : setting, 'descr':descr, 'language':language, 'chat_link' : chat_link, 'creators':[u.id, 3], **proj_kwargs })#instatiating the specific project
    db.session.add(project)
    db.session.commit() #so that project.id can be extracted later
    project.tag_update(Tag, 'tags', tags)

    membership = ProjMember(user_id=u.id, project_id = project.id, rank_id=3,position_id=Position.query.filter_by(name='Lead').first().id)
    u.member_of.append(membership)
    db.session.commit()

def make_request(user, proj, kind = 'request', msg = hash(datetime.now())):
    proj = Project.query.get_or_404(proj) 
    
    if type(user) != int:
        u = User.query.filter_by(username=user).first_or_404() #this is either the username requesting or the one invited
    else:
        u = User.query.get_or_404(user)

    if kind == 'invite':
        r = JoinRequest(kind='invite',msg=msg,status='pending')
        r.project = proj
        r.user = u
        u.send_request(proj,r,kind='invite',u_inv=u) # works like invited user is sending request to themselves
        db.session.commit()
    elif kind == 'request':
        r = JoinRequest(kind='request',msg=msg,status='pending')
        r.project = proj
        r.user = u
        u.send_request(proj,r)
        db.session.commit()

def delete_request(user_id, project_id):
    x = JoinRequest.query.filter_by(user_id=user_id,project_id=project_id).first_or_404()
    db.session.delete(x)
    db.session.commit() 

# proj = Project.query.filter_by(name='Bo project').first()



# invites = u.proj_requests.filter_by(kind='invite') 
# requests = JoinRequest.query.join(ProjMember,
#             (JoinRequest.project_id == ProjMember.project_id)).filter(
#                 ProjMember.user_id == u.id)


### ADD PROJECT TO DB ###

if 0:
    proj_kwargs = {'pace':'quarter','learning_category':'math',
                    'subject':None,
                    'resource':'a book'}
    add_proj(name= 'BriReqs2', proj_model=Learning, descr='Description here',
            category='learning',skill_level='any',setting = 'casual',language=None, 
            chat_link = None, proj_kwargs=proj_kwargs)

if 0:
    m = ProjMember(user_id=u.id, rank_id=3, project_id = proj.id,position_id=1)
    u.member_of.append(m)
    db.session.commit()
    r = JoinRequest(kind='request',msg='hello',status='pending')
    r.project = proj
    r.user = u
    u.send_request(proj, r)

# task = ScrumTask(project_id=2, user_id=1, text="doitNOW", task_type="Done")
# db.session.add(task)
# db.session.commit()
if 0:
    q= [i.text for i in x.scrum_board]
    q = ScrumTask.query.filter_by(project_id=2).all()
    q = x.scrum_board.filter_by(task_type='Done').all()
    print([i.text for i in q])

u = User.query.filter_by(username='bo').first()

if 0:
    u.tag_update(Tag, 'tags', ['ios', 'cooking', 'java','python','javascript','sql','vue'])
    db.session.commit()

add_proj('TESSS26', SoftwareDev,'easy','casual','OKO4K', 'french',None,['javascript','mongo-db'], dict()) #,{'sub_category':None}
print(list(Project.query.get(58).creators))
# x = Resource(name='Supervised Learning Cheatsheet', link='https://stanford.edu/~shervine/teaching/cs-229/cheatsheet-supervised-learning')
# db.session.add(x)
# db.session.commit() #so that project.id can be extracted later
# x.tag_update(Tag, 'tags', ['machine-learning','supervised-learning'])
# db.session.commit()
# q = Project.query.get()
# x.scrum_board.append()
# print(x.to_dict())
# print(tag_names)
# print(Tag.query.filter_by(name='math').first())

# x= Project.query.get(44)
# print(x.tag_list)
# print(getattr(x,'tags'), flush=1)

#projects = Project.query.all()     

