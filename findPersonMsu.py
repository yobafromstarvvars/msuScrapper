#! python3

import requests, bs4, re, shelve, sys, pprint, os, traceback, datetime
import config
import logging as l

l.basicConfig(level=l.DEBUG, format='    %(levelname)s %(message)s')
l.debug('PROGRAM STARTS')
#l.disable(l.DEBUG)

faculties_link = 'https://cpk.msu.ru/daily'


def get_fac_links():
	'''
	Parse html of the 'faculties_link' and sort faculty links in a dictionary
	'''
	l.debug('Entering "get_fac_links" function.')

	# Download faculty names from the faculties_link
	fac_links_un = requests.get(faculties_link)
	fac_links_un.raise_for_status()
	fac_links_un = bs4.BeautifulSoup(fac_links_un.text, 'html.parser')
	# Unsorted links
	fac_links_un = fac_links_un.select('a')
	# Sorted links
	fac_links_sorted = {
		'bachelor': [],
		'master': [],
		'second': []
		}
	for i in range(len(fac_links_un)):
		# Separate the link
		link = fac_links_un[i]#.get('href')
		link_list = link.get('href').split(os.sep) 
		# Find links that bring you to the names
		if len(link_list) == 5 and link_list[4].startswith('dep_'):
			# Save bachelors links
			if link_list[4].endswith('bs'):
				fac_links_sorted['bachelor'].append(link)
			# Save masters links
			elif link_list[4].endswith('m'):
				fac_links_sorted['master'].append(link)
			# Save second links
			elif link_list[4].endswith('2v'):
				fac_links_sorted['second'].append(link)

	l.debug('Ending "get_fac_links" function.')

	return fac_links_sorted


def get_students(links):
	'''
	Find students on faculty pages. Return total count of students, invalid names, student list
	'''

	l.debug('Entering \'get_students\' function.\n')

	students = {}
	# How many names found. Doesn't include numbering.
	invalid = []
	name_re = re.compile(r'(\w|-)+\s(\w|-)+\s?(\w|-)*')
	count_total = 0
	# How many faculties found
	count_fac = 0
	# Count how many specialties are found for an overview.
	count_spe = 0
	count_err = 0

	l.debug(links)
	for link in links:
		count_fac = 0
		faculty = link.text
		link = link.get('href')
		l.debug('='*40)
		l.info(f'Faculty: {faculty}')
		l.info(f'Link: {link}')
		l.debug('='*40)

		res = requests.get(link)
		res.raise_for_status()
		soup = bs4.BeautifulSoup(res.text, 'html.parser')
		# Make a list of stude
		names = soup.select('td')
		# Create a faculty in the dict
		students.setdefault(faculty, {})
		# Total name count in a fac
		count_fac_total = int(len(names)/2)

		for name in names:
			if name_re.search(name.text):
				# Find specialty
				specialty = name.find_previous('h3').text

				# If the name is under a specialty that doesn't exist in the 'students' dict, add to students[faculty] dict.
				if specialty not in students[faculty].keys():
					l.debug(f'({specialty}) doesn\'t exist in ({faculty}). Creating...')
					students[faculty][specialty] = []
					# Count how many specialties are found for an overview.
					count_spe += 1
				try:
					l.debug(f'Adding {name.text} from ({specialty}) specialty.')
					students[faculty][specialty].append(name.text)
				# Ignore an error, but log it
				except Exception as ex:
					count_err += 1
					l.error(f'Failed to add {name.text}.')
					try:
						l.error(f'1. {faculty} in "students": {faculty in students}')
						l.error(f'2. {specialty} in "students": {specialty in students[faculty]}')
						l.error(f'3. {name.text} in "students":  {name.text in students[faculty][specialty]}')
					except: pass

				# How many students are found
				count_total += 1
				count_fac += 1

				l.debug(f'Successfully added name ({count_fac}/{count_fac_total}) {name.text} to specialty {specialty}')
			else:
				# If not a name
				if not name.text.endswith('.'):
					invalid.append(name)

		l.debug('='*40)
		l.debug(f"{count_fac} names were added from ({faculty}) faculty." + 
			f"Invalid names: {count_fac_total-count_fac}; Total names: {count_total}.")
		l.debug('='*40)

	
	l.debug(f'Total: ' +
		f'{len(students)} facultie(s); ' +
		f'{count_spe} specialtie(s); ' +
		f'{count_total} student(s); ' +
		f'{len(invalid)} invalid name(s); ' +
		f'{count_err} error(s).')	

	return_var = {
		'students': students,
		'invalid': invalid,
		'count_total': count_total,
	}
	l.debug('End of \'get_students\' function.')
	return return_var


def save_to_hd(data, filename=''):
	'''
	Write the given data to hard drive with shelve
	'''
	l.debug('Entering "save_to_hd" function.')
	date = datetime.date.today()
	year = date.strftime("%Y")
	l.debug(f'Filename is made out of: {config.filename_prefix} + {year} + {sys.argv[1]}')

	try:
		if filename == '':
			filename = config.filename_prefix + year + sys.argv[1]
		filenamepy = filename + '.py'
	except Exception as ex:
		l.error(f'Failed to create filename {filename}.')
		l.error(f'Exception: {ex}')
		l.error(traceback.format_exc())
		return
	else:
		try:
			with open(filenamepy, 'w') as f:
				l.debug(f'{filenamepy} file is created.')
				f.write('# Students who sumbitted applications to get into Moscow State University in 2022.\n\n')
				f.write('count = ' + pprint.pformat(data['count_total']) + '\n')
				f.write('invalid = ' + pprint.pformat(data['invalid']) + '\n')
				f.write('students = ' + pprint.pformat(data['students']) + '\n')
		except Exception as ex:
			l.error(f'Failed to write {filenamepy}.')
			l.error(f'Exception: {ex}')
		else:
			# If "save_to_hd" is imported, also use shelve to save.
			if __name__ != '__main__':
				with shelve.open(filename) as shelveFile:
					shelveFile['students'] = data['students']
					shelveFile['invalid'] = data['invalid']
					shelveFile['count_total'] = data['count_total']
	
	l.debug(f'{filename} has been successfully written.')
	l.debug('Ending of "save_to_hd" function.')


def find_by_name(target_name, student_data):
	'''
	Loop through the student_data and find objects with the target_name.
	Save them in a dictionary and return it.
	'''
	l.debug('Entering "find_by_name" function.')

	target_name_re = re.compile(r'\W%s\W' % target_name, re.IGNORECASE)
	l.debug(f'Created regular expression: {target_name_re}')
	# List of dictionaries with name, faculty, specialty
	matches = []

	# Tracking 
	count_found = 0

	l.debug('Searching for %s' % target_name)
	for key, value in student_data.items():
		l.debug(f'Iterating through dictionary: {key} - {str(value)[:50]}...')
		if key == 'students':
			# value is {faculty: {specialty : [names]}}
			for faculty, values in value.items():
				l.debug(f'Iterating through values of ({faculty}) faculty.')

				for specialty, names in values.items():
					l.debug(f'Iterating through values of ({specialty}) specialty.')
					
					for name in names:
						# Does name include 'target_name'?
						name_match = target_name_re.search(name)

						l.debug(f'{target_name} == {name}: {name_match}')

						if name_match:
							count_found += 1
							matches.append(
								{'name': name.title(),
								'faculty': faculty,
								'specialty': specialty,})
							l.debug(f'Found match: {name}. Added to "matches" ({count_found} item(s) long).')

	l.debug(f'Matches list of dictionaries: {matches}')
	l.debug('='*30)
	l.debug(f'Found: {count_found} names.')
	l.debug("Ending the 'find_by_name' function.")
	return matches
		

def main():
	'''
	Handles user input. Calls run().
	'''
	l.debug(f'{len(sys.argv)} attributes. Sys.argv={sys.argv}')
	error_msg = 'Unknown attribute. Type "help" to see available options.'	
	argv_len = len(sys.argv)

	try:
		if argv_len >= 1:
			# Set default variables
			section = 'all' #bachelor, master, second
			filename = ''
			target_name = config.search_name	

			if argv_len >= 2:
				section = sys.argv[1] #bachelor, master, second

				if sys.argv[1] == 'help':
					print('''2022 August 13th, Vitaly Kungurtsev
This program searches msu website for applicants' names and searches for whatever name a user provides.
1st attribute:\tbachelor, master, second, all;
2nd attribute:\tfilename where data will be saved. Type --name to skip filename;
3rd attribute:\ttarget name of search.''')
					return

				if sys.argv[1] not in ['bachelor', 'master', 'second', 'all']:
					raise Exception(error_msg)

				if argv_len >= 3:
					filename = sys.argv[2] #file where student_data is saved
					if filename == '--name': filename = ''
					if argv_len >= 4:
						target_name = ' '.join(sys.argv[3:]) #name to search for
			run(section, filename, target_name)
	except Exception as ex:
		l.debug(ex)
		l.debug(traceback.format_exc())
		#print(error_msg)


def run(section='all', filename='', target_name='АРИНА'):
	'''
	Handles the calls of the main functions
	'''
	l.debug('Entering "run()" function')

	fac_links_sorted = get_fac_links()
	links = []

	if section == 'all':
		for list_of_links in fac_links_sorted.values():
			links += list_of_links
	else: 
		links = fac_links_sorted[section]

	student_data = get_students(links)
	save_to_hd(student_data, filename)
	matches = find_by_name(target_name, student_data)

	l.debug('Ending "run()" function')



if __name__ == '__main__':
	main()




l.debug('PROGRAM ENDS')


# download list with the matches
# try parse html except: take data from the file
# find matches' lastnames in Friday Point vk members list
# ..

"""
user-agent
min(5, len(elems)) #returns length of the 'elems' if it's smaller than 5
endswith('e')
os.makedirs('directory', exist_ok=True) #if exists, don't raise an exception)

webbrowser
	open('link')
requests
	raise_for_status()
	get('link')
	status_code
	codes.ok
	text
	iter_content(100000) #returns a chunk of bites. You have to open a file in 'wb' mode to save chunks to it
bs4
	BeautifulSoup(htmltext, 'html.parser')
	select('div') #returns a list
	getText() #returns text in between open and close tags
	attrs #returns a dict of attrs
	get('attribute') #return the attribute's value
selenium
	from selenium imprt webdriver
	from selenium.webdriver.common.by import By
	from selenium.webdriver.common.keys import Keys
	browser = webdriver.Firefox() #browser is webdriver obj
	browser.get('link')
	browser.find_element(By.ID, 'user_name')
	click()
	send_keys(keys)
		DOWN 
		UP 
		LEFT 
		RIGHT
		ENTER
		RETURN
		HOME
		END
		PAGE_DOWN
		PAGE_UP
		ESCAPE
		BACK_SPACE
		DELETE
		F1
		F2
		TAB
	submit() #no matter what element you submit it unless you're in the form
	browser.back()
	browser.forward()
	browser.refresh()
	browser.quit()
	tag_name
	get_attribute(name)
	text
	clear() #clears text typed into a field
	is_displayed() #if element is visible
	is_enabled()
	is_selected() #for checkbox or radio buttons
	location #dictionary with keys x and y for the position of the element in the page

"""
