#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import urllib
import webapp2
import os
import jinja2
import cgi
import re
import session_module

from webapp2_extras import sessions
from google.appengine.ext import ndb

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers


template_dir = os.path.join(os.path.dirname(__file__), 'html')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)


MAIN_PAGE_HTML = """\

<html>
    <head>
		<meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="/bootstrap/css/bootstrap.css">
        <link rel="stylesheet" href="/bootstrap/css/bootstrap-theme.css">
    </head>

    <body>
    <br/><br/>
        <div class="container">
          <div class="jumbotron">
            <h1>My Album</h1>
            <p>Crea y guarda todas las fotos que desees!</p>
          </div>
              <div class="row">
                <div class="col-sm-4">
                  <h3>Login</h3>
                  <a href="/login"> <img src="/images/login.jpg" class="img-circle" alt="Login" width="204" height="156"/></a>
                  </br>
                  <p>Haz login para poder mirar el album...</p>
                  <p>Inserta, elimina o modifica tus fotos.</p>
                </div>
                <div class="col-sm-4">
                  <h3>Register</h3>
                  <a href="/reg"><img src="/images/register.png" class="img-circle" alt="Register" width="204" height="156"/> </a>
                    </br>
                  <p>Registrate para poder crear tu album...</p>
                  <p>Si te registrar podras ver y manipular fotos.</p>
                </div>
                <div class="col-sm-4">
                  <h3>Album</h3>
                  <a href="/mostrarPublicas"><img src="/images/album.jpg" class="img-circle" alt="Album" width="180" height="156"> </a>
                    </br>
                  <p>Visita los albumes de tus amig@s</p>
                  <p>En este apartado podras visualizar las fotografias de tus conocidos.</p>
                </div>
            </div>
            <br/><br/><br/>
        <div class="panel panel-default">
            <div class="panel-footer">
                <div class="row">
                    <div class="col-sm-4">
                        <h4>Creadoras</h4><br/>
                        <p>Marta Garcia</p>
                        <p>Beatriz Pe&ntilde;as</p>
                    </div>
                </div>
            </div>
        </div>

    </div>
    </body>
</html>
"""



def validar_nombre(nombre):
    return USER_RE.match(nombre)


def validar_email(email):
    return EMAIL_RE.match(email)


def validar_password(password):
    return PASSWORD_RE.match(password)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
PASSWORD_RE = re.compile(r"^.{3,20}$")


def escape_html(s):
    return cgi.escape(s, quote=True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class Handler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(MAIN_PAGE_HTML)

class Album2(webapp2.RequestHandler):
    def get(self):
        self.write.render("album.html")

class Usuario(ndb.Model):

    nombre = ndb.StringProperty()
    apellido = ndb.StringProperty()
    email = ndb.StringProperty()
    password = ndb.StringProperty()
    creado=ndb.DateTimeProperty(auto_now_add=True)

class logoutHandler(session_module.BaseSessionHandler, Handler):
    def get(self):
        del self.session['user']
        self.redirect('/')


class loginHandler(session_module.BaseSessionHandler, Handler):

    def get(self):
        if self.session.get('user') == None:
            self.write(render_str("login.html") % {"email": "", "password": "", "error_email": "","error_password": ""})
        else:
            print(self.session.get('user'))
            self.redirect('/')
            self.response.write("Usuario ya loggeado")

    def post(self):
        user_email = self.request.get('email')
        user_password = self.request.get('password')

        error = False

        if not validar_email(user_email):
            error_email = "Email incorrecto"
            error = True
        else:
            error_email = ""

        if not validar_password(user_password):
            error_password = "Password incorrecto"
            error = True
        else:
            error_password = ""

        if error:
            self.write(render_str("register.html") % {"email": user_email,
                                                      "password": "",
                                                      "error_email": error_email,
                                                      "error_password": error_password})
        else:

            users = Usuario.query(Usuario.email == user_email, Usuario.password== user_password)

            if (users.count() == 0):
                self.response.write("Usuario no encontrado")
            else:
                for u in users:
                    print(u.nombre)
                    if (u.password == user_password):
                        if self.session.get('user') == None:
                            self.session['user'] = user_email
                            self.session['nombre'] = u.nombre

                        self.write(render_str('album.html') % {"nombre":self.session.get('nombre')})
                    else:
                        self.redirect('/')


class regHandler(Handler):

    def write_form(self):
        self.write(render_str("register.html") % {"nombre":"",
                    "apellido":"",
                    "email":"",
                    "password":"",
                    "password2": "",
                    "error_nombre":"",
                    "error_email": "",
                    "error_password": ""})

    def get(self):
        self.write_form()

    def post(self):

        user_username = self.request.get('nombre')
        user_name = self.request.get('apellido')
        user_email = self.request.get('email')
        user_password = self.request.get('password')

        error = False

        if not validar_nombre(user_username):
            error_nombre = "Nombre incorrecto"
            error = True
        else:
            error_nombre = ""

        if not validar_email(user_email):
            error_email = "Email incorrecto"
            error = True
        else:
            error_email = ""

        if not validar_password(user_password):
            error_password = "Password incorrecto"
            error = True
        else:
            error_password = ""

        if error:
            self.write(render_str("register.html") % {"nombre": user_username,
                                                      "apellido": user_name,
                                                      "email": user_email,
                                                      "password": "",
                                                      "password2": "",
                                                      "error_nombre": error_nombre,
                                                      "error_email": error_email,
                                                      "error_password": error_password})
        else:

            user = Usuario.query(Usuario.email == user_email).count()

            if user == 0:
                u = Usuario()
                u.nombre = user_username
                u.apellido = user_name
                u.email = user_email
                u.password = user_password
                u.put()
                #self.response.out.write( "Bienvenido %s <p> ya estas registrado </p>" % user_username)
                #self.response.out.write("<div class="alert alert-success"> <strong>Success!</strong> Indicates a successful or positive action.</div>")
                self.redirect("/")

            else:
                self.response.out.write("Ya estabas registrado")



class Album(ndb.Model):
	name = ndb.StringProperty(indexed=False)
	owner = ndb.StringProperty(indexed=True)

class Image(ndb.Model):
    album = ndb.StringProperty()
    access = ndb.StringProperty()
    blob_key = ndb.BlobKeyProperty()
    def get_key(self):
      return self.key.id()



class createAlbum (session_module.BaseSessionHandler, Handler):
    def get(self):
        if self.session.get('user') == None:
            self.redirect('/')
        else:
            self.write(render_str('crearAlbum.html'))

    def post(self):
        if self.session.get('user'):
            owner = self.session.get('user')
            name = self.request.get('name')
            newAlbum = Album()
            newAlbum.name = name
            newAlbum.owner = owner
            newAlbum.put()
            #self.redirect('/subirFotos')
            self.write(render_str('album.html'))

class uploadPhoto(blobstore_handlers.BlobstoreUploadHandler, session_module.BaseSessionHandler, Handler):
    def get(self):
        if self.session.get('user') == None:
            self.redirect('/')
        else:
			albums = Album.query(Album.owner == self.session.get('user'))
			upload_url = blobstore.create_upload_url('/subirFotos')

			template_values = {
			'albums': albums,
			'url': upload_url,
			}
			template = jinja_env.get_template('subir.html')
			self.response.write(template.render(template_values))

    def post(self):

        if self.session.get('user'):
            album = self.request.get('album')
            upload_files = self.get_uploads()
            blobstore.create_upload_url('/upload')
            access = self.request.get("access")
            blob_info = upload_files[0]
            image = Image(album=album, access=access, blob_key=blob_info.key())
            image.put() 
            self.write(render_str('album.html'))
        else:
            self.redirect('/')
            
class mostrarFotosPublicas(session_module.BaseSessionHandler,Handler):
            def get(self):
                images = Image.query(Image.access=="public")
                self.render('mostrarFotosPublicas.html',images=images)
                #for i in images:
                #self.write("<img src='/fotosAlbum?id="+str(i.get_key())+"'/>")

class mostrarFotos(session_module.BaseSessionHandler,Handler):
    def get(self):
        if self.session.get('user') == None:
            self.redirect('/')
        else:
            albums = Album.query(Album.owner == self.session.get('user'))
            self.render('mostrarAlbum.html',albums=albums)
    def post(self):
        album = self.request.get("album")
        images = Image.query(Image.album==album)
        for i in images:
          self.write("<img src='/fotosAlbum?id="+str(i.get_key())+"'/>")

class fotosAlbum(session_module.BaseSessionHandler, blobstore_handlers.BlobstoreDownloadHandler):
  def get(self):
    id_im = self.request.get("id")
    foto = Image.get_by_id(int(id_im))
    if not foto:
      return abort(404)
    else:
      if not blobstore.get(foto.blob_key):
        return abort(404)
      else:
        self.send_blob(foto.blob_key)

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'my-super-secret-key',
}

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/album', Album2),
    ('/login', loginHandler),
    ('/logout', logoutHandler),
    ('/reg',regHandler),
    ('/crearAlbum', createAlbum),
    ('/subirFotos', uploadPhoto),
    ('/mostrarFotos', mostrarFotos),
    ('/fotosAlbum', fotosAlbum),
    ('/mostrarPublicas', mostrarFotosPublicas)
], config = session_module.myconfig_dict, debug=True)