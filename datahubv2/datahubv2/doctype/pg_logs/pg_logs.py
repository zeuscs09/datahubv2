# Copyright (c) 2025, Ton and contributors
# For license information, please see license.txt

import frappe
import psycopg2
import time
from frappe.model.document import Document
from datahubv2.lib.pg_connect import log_to_postgres


class PGLogs(Document):
	pass


@frappe.whitelist()
def test_postgresql_connection(host, port, db_name, user_name, password):
	"""
	Test PostgreSQL database connection with the provided configuration
	
	Args:
		host (str): PostgreSQL server host
		port (str): PostgreSQL server port
		db_name (str): Database name
		user_name (str): Database username
		password (str): Database password
	
	Returns:
		dict: Test result with success status and details
	"""
	
	result = {
		'success': False,
		'host': host,
		'port': port,
		'database': db_name,
		'error': None,
		'response_time': None,
		'server_version': None,
		'tables_count': None,
		'tested_at': frappe.utils.now()
	}
	
	start_time = time.time()
	conn = None
	
	try:
		# Convert port to integer
		try:
			port_int = int(port) if port else 5432
		except ValueError:
			result['error'] = f'Invalid port number: {port}'
			return result
		
		# Connection parameters
		connection_params = {
			'host': host,
			'port': port_int,
			'database': db_name,
			'user': user_name,
			'password': password,
			'connect_timeout': 10  # 10 seconds timeout
		}
		
		# Attempt to connect
		conn = psycopg2.connect(**connection_params)
		
		# Calculate response time
		end_time = time.time()
		result['response_time'] = round((end_time - start_time) * 1000, 2)
		
		# Connection successful
		result['success'] = True
		
		# Get server version
		try:
			cursor = conn.cursor()
			cursor.execute("SELECT version();")
			version_info = cursor.fetchone()[0]
			result['server_version'] = version_info.split(',')[0]  # Get main version info
			
			# Count tables in public schema
			cursor.execute("""
				SELECT COUNT(*) 
				FROM information_schema.tables 
				WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
			""")
			result['tables_count'] = cursor.fetchone()[0]
			
			cursor.close()
			
		except Exception as e:
			# Even if we can't get additional info, connection is still successful
			frappe.logger().warning(f"Could not get PostgreSQL server info: {str(e)}")
	
	except psycopg2.OperationalError as e:
		error_msg = str(e).strip()
		if 'timeout expired' in error_msg.lower():
			result['error'] = 'Connection timeout - Unable to reach PostgreSQL server within 10 seconds'
		elif 'authentication failed' in error_msg.lower():
			result['error'] = 'Authentication failed - Invalid username or password'
		elif 'database' in error_msg.lower() and 'does not exist' in error_msg.lower():
			result['error'] = f'Database "{db_name}" does not exist'
		elif 'connection refused' in error_msg.lower():
			result['error'] = f'Connection refused - PostgreSQL server may not be running on {host}:{port}'
		elif 'no route to host' in error_msg.lower():
			result['error'] = f'No route to host - Unable to reach {host}'
		else:
			result['error'] = f'Connection error: {error_msg}'
	
	except psycopg2.Error as e:
		result['error'] = f'PostgreSQL error: {str(e).strip()}'
	
	except Exception as e:
		result['error'] = f'Unexpected error: {str(e)}'
		frappe.log_error(f'PostgreSQL test connection error: {str(e)}', 'PG Logs Connection Test')
	
	finally:
		# Close connection if it was opened
		if conn:
			try:
				conn.close()
			except Exception:
				pass
		
		# Calculate response time if not set
		if result['response_time'] is None:
			end_time = time.time()
			result['response_time'] = round((end_time - start_time) * 1000, 2)
	
	# Log the test result to PostgreSQL (if the connection test was successful)
	try:
		log_data = {
			'test_type': 'postgresql_connection_test',
			'host': host,
			'port': port_int,
			'database': db_name,
			'username': user_name,
			'success': result['success'],
			'response_time_ms': result['response_time'],
			'server_version': result['server_version'],
			'tables_count': result['tables_count'],
			'error_message': result['error'],
			'tested_by': frappe.session.user,
			'tested_at': result['tested_at']
		}
		
		# Only log to PostgreSQL if we have a working PG connection utility
		# (avoid recursive calls if testing the same DB that stores logs)
		if result['success']:
			log_to_postgres(
				ref_id=f"pg_test_{int(time.time())}_{frappe.session.user}",
				ref_module="postgresql_connection_test",
				json_data=log_data
			)
		
	except Exception as e:
		frappe.log_error(f'Failed to log PostgreSQL test to database: {str(e)}', 'PostgreSQL Test Log Error')
	
	return result


@frappe.whitelist()
def get_connection_status():
	"""
	Get the current PostgreSQL connection status based on saved configuration
	
	Returns:
		dict: Connection status information
	"""
	try:
		pg_config = frappe.get_single("PG Logs")
		
		if not all([pg_config.host, pg_config.port, pg_config.db_name, pg_config.user_name, pg_config.password]):
			return {
				'configured': False,
				'message': 'PostgreSQL configuration is incomplete'
			}
		
		# Test connection with saved config
		result = test_postgresql_connection(
			pg_config.host,
			pg_config.port,
			pg_config.db_name,
			pg_config.user_name,
			pg_config.password
		)
		
		return {
			'configured': True,
			'connected': result['success'],
			'message': 'Connection successful' if result['success'] else result['error'],
			'response_time': result['response_time'],
			'server_version': result.get('server_version')
		}
		
	except Exception as e:
		return {
			'configured': False,
			'connected': False,
			'message': f'Error checking connection status: {str(e)}'
		}
