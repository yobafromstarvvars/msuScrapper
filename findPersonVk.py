import vk_api, pprint
from config import *

session = vk_api.VkApi(token=token)
vk = session.get_api()


def get_user_status(user_id):
	status = vk.status.get(user_id=user_id)
	print(status)


def get_group_members(group_id):
	# Get group members info
	group_members = []
	page = 0
	count = vk.groups.getMembers(group_id=group_id)['count']
	required_fields = ['first_name', 'last_name', 'sex']
	
	# Get group members with certain fields
	while count > len(group_members):
		offset = page * 1000
		group_members_ids = vk.groups.getMembers(group_id=group_id, 
												 offset=offset,)
		group_members += vk.users.get(user_ids=group_members_ids['items'], 
									  fields=required_fields)
		page += 1

	return count, group_members


def get_user_groups(user_id):
	groups = vk.groups.get(user_id=user_id, extended=1)
	return groups


def get_group_id_by_name(groups, group_name):
	# returns a dictionary {listId: groupId}
	# 'groups' has to be a list of dictionaries
	i = 0
	group_ids = []
	for group in groups:
		if group['name'] == group_name:
			group_ids.append(i)
			group_ids.append(group['id'])
			break
		i += 1
	return group_ids


def default_gender(member):
	# Make female lastname into male lastname
	sex = member['sex']
	first_name = member['first_name']
	last_name = member['last_name']

	if member['sex'] == 1:
		if last_name[-3:] == 'aya':
			last_name = last_name[:-3] + 'y'
		elif last_name[-1:] == 'a':
			last_name = last_name[:-1]
		elif last_name[-2:] == 'na':
			last_name = last_name[:-2] 

		member['last_name'] = last_name
	return member


def find_same_last_name(group_members, searchname):
	# Iterate through group members and find users with the same last name
	# Count names
	deleted_members_count = 0
	last_names = {}
	for member in group_members:
		if member['first_name'] == 'DELETED' and member['last_name'] == '':
			deleted_members_count += 1
		member = default_gender(member)
		last_names.setdefault(member['last_name'], {'count':0,'male':0,'female':0,'names':[]})
		last_names[member['last_name']]['count'] += 1
		last_names[member['last_name']]['names'].append(member['first_name'])
		# if female
		if member['sex'] == 1:
			last_names[member['last_name']]['female'] += 1
		# if male
		elif member['sex'] == 2:
			last_names[member['last_name']]['male'] += 1
			
	# Save only repeated names
	same_last_names = {}
	for k, v in last_names.items():
		if v['count'] > 1:
			for name in v['names']:
				if searchname in name:
					same_last_names[k] = v

	return same_last_names, deleted_members_count


def print_results(results, total):
	# Pretty print the results with some 'total' info after it
	# results = (matches, deleted)
	pprint.pprint(results[0])
	pprint.pprint('========================================')

	total = f'Total: {total}'
	match = f'Match: {len(results[0])}'
	deleted = f'Deleted: {results[1]}'
	print(match, deleted, total, sep='\n')



user_groups = get_user_groups(user_id)

group_ids = get_group_id_by_name(user_groups['items'], vk_group_name) # returns: listId, groupId

total, group_members = get_group_members(group_ids[1]) # group_members is a list

results = find_same_last_name(group_members, vk_search_name) # returns: matches, deleted

print_results(results, total)
