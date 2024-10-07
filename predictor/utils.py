from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('DB_URL')
key = os.getenv('DB_KEY')
supabase: Client = create_client(url, key)

def get_college_choices():
    response = supabase.table('colleges').select('college_id', 'college_name').order('college_name').execute()
    colleges = response.data
    return [(None, 'Select a college')] + [(college['college_id'], college['college_name']) for college in colleges]

def get_branch_choices():
    response = supabase.table('branches').select('branch_id', 'branch_name').order('branch_name').execute()
    branches = response.data
    return [(None, 'Select a branch')] + [(branch['branch_id'], branch['branch_name']) for branch in branches]
