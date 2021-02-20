from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.handlers.sha2_crypt import sha256_crypt
from functools import wraps

#Kullanıcı Giriş Decoratörü
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:
            
            return f(*args, **kwargs)

        else:
            flash('Bu sayfayı görüntülemek için giriş yapınız','danger')
            return  redirect(url_for('login'))
    return decorated_function
#Profil Bilgileri Formu
class ProfilForm(Form):
    username=StringField('Yeni Kullanıcı adı',validators=[validators.Length(min=3,max=20)])
    experience=StringField('Deneyim',validators=[validators.Length(min=3,max=20)])
    eng_level=StringField('İngilizce seviyesi',validators=[validators.Length(min=3,max=35)])
    skill1=StringField('Bilgisayar Bilgisi',validators=[validators.Length(min=3,max=35)])
    skill2=StringField('',validators=[validators.Length(min=3,max=35)])
    skill3=StringField('',validators=[validators.Length(min=3,max=35)])
    ins=StringField('İnstagram adresi')
    twit=StringField('Twitter adresi')
    linked=StringField('Linkedin adresi')





#Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name=StringField('İsim Soyisim',validators=[validators.Length(min=4,max=25)])
    username=StringField('Kullanıcı Adı',validators=[validators.Length(min=5,max=35)])
    email=StringField('Email Adresi',validators=[validators.Email(message='Lütfen Geçerli Email Girin.. ')])
    password=PasswordField('Parola:',validators=[
        validators.DataRequired(message='Lütfen bir parola belirleyin'),
        validators.EqualTo(fieldname='confirm',message='Parolanız uyuşmuyor')

    ])
    confirm=PasswordField('Parola Doğrula')
#Login Formu
class LoginForm(Form):
    username=StringField('Kullanıcı Adı')
    password=PasswordField('Parola')


app=Flask(__name__)
app.secret_key='ybblog'

#Aşağıdakileri yapınca Flask ile Mysql arasındaki ilişkiyi kurnuş oluyoruz.

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='ybblog'
app.config['MYSQL_CURSORCLASS']='DictCursor'

mysql=MySQL(app)



@app.route('/')
def index():
    
    return render_template('index.html')
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/dashboard')
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu='Select * From articles where author=%s'
    result=cursor.execute(sorgu,(session['username'],))
    if result>0:
        articles=cursor.fetchall()
        return  render_template('dashboard.html',articles=articles)
    else:
        return render_template('dashboard.html')




@app.route('/article/<string:id>')
def article(id):
    cursor=mysql.connection.cursor()
    sorgu='Select*From articles where id = %s'
    result=cursor.execute(sorgu,(id,))
    if result>0:
        article=cursor.fetchone()
        return render_template('article.html',article=article)

    else:

         return render_template('article.html')


@app.route('/register',methods=['GET','POST'])
def register():

    form = RegisterForm(request.form)

    if request.method == 'POST' and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        


        password=sha256_crypt.encrypt(form.password.data)

        cursor=mysql.connection.cursor()
        sorgu='Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)'
        cursor.execute(sorgu,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()
        flash('Başarıyla Kayıt oldunuz','success')

        return redirect(url_for('login'))

    else:

        return render_template('register.html',form=form)
@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm(request.form)
    if request.method=='POST':
        username=form.username.data
        password_entered=form.password.data
        cursor=mysql.connection.cursor()
        sorgu='Select * From users where username=%s'

        result=cursor.execute(sorgu,(username,))

        if result >0:
            data = cursor.fetchone()
            real_password=data['password']
            
            if sha256_crypt.verify(password_entered,real_password):
                flash('Başarıyla Giriş Yaptınız...','success')
                #oturum kontrolü 
                session['logged_in']=True
                session['username']=username
               
                return  redirect(url_for('index'))

            else:
                flash('Parolanızı Yanlış Girdiniz... ','danger')
                return  redirect(url_for('login'))




        else:
            flash('Böyle bir kullanıcı bulunmuyor','danger')
            return redirect(url_for('login'))
    else:

        return render_template('login.html',form=form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

#Makale Ekleme
@app.route('/addarticle',methods=['GET','POST'])
def addarticle():

    form=ArticleForm(request.form)
    if request.method=='POST' and form.validate():
        title=form.title.data
        content=form.content.data

        cursor=mysql.connection.cursor()

        sorgu='Insert into articles(title,author,content) VALUES(%s,%s,%s)'

        cursor.execute(sorgu,(title,session['username'],content))

        mysql.connection.commit()

        cursor.close()

        flash('Makale Başarıyla Eklendi','success')

        return redirect(url_for('dashboard'))


    else:
      
        return render_template('addarticle.html',form=form)

#Makale Silme

@app.route('/delete/<string:id>')
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu='Select * from articles where author=%s and id=%s'
    result = cursor.execute(sorgu,(session['username'],id))
    if result>0:

        sorgu2='Delete from articles where id =%s'

        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()

        return redirect(url_for('dashboard'))

    else:
        flash('Böyle bir Makale yok veya Bu işleme yetkiniz yok','danger')
        return redirect(url_for('index'))



#Makale Güncelleme
@app.route('/edit/<string:id>',methods=['GET','POST'])
@login_required
def update(id):
    if request.method=='GET':

        cursor=mysql.connection.cursor()
        sorgu='Select * from articles where id=%s and author=%s'
        result=cursor.execute(sorgu,(id,session['username']))
        if result==0:
            flash('Böyle bir makale yok veya bu işleme yetkiniz yok','danger')
            return redirect(url_for('index'))

        else:
            article=cursor.fetchone()
            form=ArticleForm()

            form.title.data=article['title']
            form.content.data=article['content']
            return render_template('update.html',form=form)
    else:
        form=ArticleForm(request.form)
        newTitle=form.title.data
        newContent=form.content.data
        sorgu2='Update articles Set title=%s,content=%s where id=%s'
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash('Makale Başarıyla Güncellendi','success')
        return redirect(url_for('dashboard'))
        
#Makale Arama

@app.route('/search',methods=['GET','POST'])
def search():

    if request.method=='GET':
        return redirect(url_for('index'))
    else:
        keyword=request.form.get('keyword')
        cursor=mysql.connection.cursor()
        sorgu="Select * From articles where title like '%"+keyword+"%' "
        result=cursor.execute(sorgu)
        if result==0:
            flash('Aranan kelimeye uygun makale bulunamadı','warning')
            return redirect(url_for('articles'))
        else:
            articles=cursor.fetchall()
            return render_template('articles.html',articles=articles)


#Makale Sayfası

@app.route('/articles')
def articles():
    cursor=mysql.connection.cursor()
    sorgu='Select * From articles'
    result=cursor.execute(sorgu)
    if result>0:
        articles=cursor.fetchall()
        return render_template('articles.html',articles=articles)
    else:
        return render_template('articles.html')

#Profil Sayfası

@app.route('/profil/<username>',methods=['GET','POST'])
@login_required
def profile(username):
    
    
    if request.method=='GET':

        cursor=mysql.connection.cursor()
        sorgu='Select * From users where username=%s'
        cursor.execute(sorgu,(session['username'],))
        user=cursor.fetchone()

        sorgu2='Select * From profiles where username=%s'
        cursor.execute(sorgu2,(username,))

        profil=cursor.fetchone()

        return render_template('profile.html',user=user,profil=profil)

    else:
        pass





        
#Profil Düzenleme
@app.route('/profil/edit/<username>',methods=['GET','POST'])
@login_required
def edit_profile(username):
    form=ProfilForm(request.form)
    if request.method == 'POST' and form.validate():
        new_username=form.username.data
        experience=form.experience.data
        eng_level=form.eng_level.data
        skill1=form.skill1.data
        skill2=form.skill2.data
        skill3=form.skill3.data
        ins=form.ins.data
        twit=form.twit.data
        linked=form.linked.data
        cursor=mysql.connection.cursor()
        sorgu='Insert into profiles(username,experience,eng_level,skill1,skill2,skill3,ins,twit,linked) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        cursor.execute(sorgu,(new_username,experience,eng_level,skill1,skill2,skill3,ins,twit,linked))
        mysql.connection.commit()
        sorgu2='Update users Set username=%s where username=%s'
        cursor.execute(sorgu2,(new_username,username))
        mysql.connection.commit()
        sorgu3='Update articles Set author=%s where author=%s'
        cursor.execute(sorgu3,(new_username,username))
        mysql.connection.commit()

        cursor.close()

        flash('Profiliniz Düzenlendi','success')
        return  redirect(url_for('index'))

    else:

        return render_template('edit_profile.html',form=form)






#Makale Form

class ArticleForm(Form):
    title=StringField('Makale Başlığı',validators=[validators.Length(min=5,max=100)])
    content=TextAreaField('Makale İçeriği',validators=[validators.Length(min=10)])







if __name__=='__main__':
    app.run(debug=True)
        
    