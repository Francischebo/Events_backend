# extensions.py - Flask Extensions Initialization
from flask_pymongo import PyMongo
import os
import pymongo
from config import Config
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt

# Initialize extensions
class _MongoWrapper:
	"""Wrapper around Flask-PyMongo to provide a reliable `db` attribute.

	Some MongoDB URIs (notably mongodb+srv without a path) may not expose a default
	database to Flask-PyMongo. This wrapper ensures `mongo.db` is always available
	after `init_app(app)` by falling back to a direct `pymongo.MongoClient` when needed.
	"""
	def __init__(self):
		self._py = PyMongo()
		self.db = None
		self.client = None

	def init_app(self, app):
		# Initialize the underlying Flask-PyMongo
		self._py.init_app(app)

		# If Flask-PyMongo did not set a db (e.g., no default DB in URI), create a fallback
		underlying_db = getattr(self._py, 'db', None)
		if underlying_db is not None:
			self.db = underlying_db
			# try to attach client/cx if available
			self.client = getattr(self._py, 'cx', None) or getattr(self._py, 'client', None)
			return

		# Fallback: build a pymongo client from config and attach a DB
		uri = app.config.get('MONGO_URI') or os.environ.get('MONGO_URI') or Config.MONGO_URI
		dbname = app.config.get('MONGO_DBNAME') or os.environ.get('MONGO_DBNAME') or getattr(Config, 'MONGO_DBNAME', 'event_management')
		
		try:
			# Try to connect with the URI as-is
			client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
			# Test connection
			client.server_info()
			self.client = client
			self.db = client[dbname]
			app.logger.info(f"Connected to MongoDB: {dbname}")
		except Exception as e:
			app.logger.warning(f"Failed to connect with URI: {e}")
			
			# Try local MongoDB as fallback
			try:
				local_uri = 'mongodb://localhost:27017/event_management'
				app.logger.info(f"Attempting fallback to local MongoDB: {local_uri}")
				client = pymongo.MongoClient(local_uri, serverSelectionTimeoutMS=5000)
				client.server_info()
				self.client = client
				self.db = client[dbname]
				app.logger.info(f"Connected to local MongoDB fallback: {dbname}")
			except Exception as e2:
				app.logger.error(f"Both Atlas and local MongoDB connections failed: {e2}")
				# Don't raise - let app start without DB for now
				self.client = None
				self.db = None

	def __getattr__(self, name):
		# Proxy other attributes/methods to the underlying PyMongo instance
		return getattr(self._py, name)


mongo = _MongoWrapper()
jwt = JWTManager()
# Do not force `async_mode` here – allow Flask-SocketIO to auto-detect the best
# available async framework (eventlet/gevent) for production performance.
socketio = SocketIO()
bcrypt = Bcrypt()
