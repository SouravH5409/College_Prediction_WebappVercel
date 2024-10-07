from django.shortcuts import render, redirect
from .forms import UserInputForm
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from supabase import create_client, Client
from django.contrib.auth import logout
import os
from dotenv import load_dotenv
from django.contrib.auth.decorators import login_required

load_dotenv()
url = os.getenv('DB_URL')
key = os.getenv('DB_KEY')
supabase: Client = create_client(url, key)

GMEAN = [67.47, 67.07, 62.4]
GSD = [15.17, 15.9, 19.78]
MEAN = [
    [67.9, 69.9, 61.2],
    [70.5, 69.3, 64.6],
    [67.78, 64.66, 66.5]
]
SD = [
    [16.16, 16.29, 20.45],
    [13.98, 14.5, 20.8],
    [17.2, 16.01, 18.54]
]
board_limits = {
    'State': [120, 120, 100],  
    'CBSE': [100, 100, 100],   
    'ICSE': [100, 100, 100],   
}

def home_view(request):
    return render(request, 'predictor/home.html')

@login_required
def user_input_view(request):
    if request.method == 'POST':
        form = UserInputForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            board = cleaned_data['board']
            physics_marks = cleaned_data['physics_marks']
            chemistry_marks = cleaned_data['chemistry_marks']
            maths_marks = cleaned_data['maths_marks']
            keam_score = cleaned_data['keam_score']
            branch = cleaned_data['preferred_branch']
            college_type = cleaned_data['college_type']
            preferred_college = cleaned_data['preferred_college']

            total_pcm_marks = physics_marks + chemistry_marks + maths_marks

            board_choices = ['STATE', 'CBSE', 'ICSE']  
            if board in board_choices:
                stream_index = board_choices.index(board)  
                predicted_rank = predict_rank(physics_marks, chemistry_marks, maths_marks, keam_score, stream_index)
                
                request.session['user_input'] = {
                    'total_pcm_marks': total_pcm_marks,
                    'keam_score': keam_score,
                    'predicted_rank': predicted_rank,
                    'branch': branch,
                    'college_type': college_type,
                    'preferred_college': preferred_college,
                }
                return redirect('results')
            else:
                form.add_error('board', 'Invalid board selected.')
        else:
            print(form.errors)
    else:
        form = UserInputForm()
    return render(request, 'predictor/predict_form.html', {'form': form})

def predict_rank(physics, chemistry, maths, keam, stream_index):
    board_limits = {
        0: [120, 120, 100],  
        1: [100, 100, 100],  
        2: [100, 100, 100]   
    }

    limits = board_limits.get(stream_index, [100, 100, 100])  

    keam_scaled = (keam * 300) / 960

    scaled_marks = [
        (physics * 100) / limits[0],   
        (chemistry * 100) / limits[1], 
        (maths * 100) / limits[2]      
    ]

    adjusted_marks = []
    for i in range(3):
        adjusted_mark = GMEAN[i] + GSD[i] * ((scaled_marks[i] - MEAN[stream_index][i]) / SD[stream_index][i])
        adjusted_marks.append(adjusted_mark)

    total_score = keam_scaled + sum(adjusted_marks)
    total_score = round(total_score, 2)

    samrank = [1, 1, 5, 15, 58, 750, 1680, 4303, 7195, 14821, 19430, 25789, 30545, 36200, 42854, 46686]
    sammark = [600, 585, 576, 569, 556.72, 509.61, 400.54, 364.35, 342.42, 309.69, 291.13, 273.28, 255.17, 239, 174.9, 166]

    lower_index = 0
    upper_index = len(sammark) - 1

    for i in range(len(sammark)):
        if sammark[i] >= total_score:
            lower_index = i
        if sammark[i] <= total_score:
            upper_index = i
            break

    if lower_index == upper_index:
        rank = samrank[lower_index]
    else:
        rank = samrank[lower_index] + ((samrank[upper_index] - samrank[lower_index]) / 
               (sammark[upper_index] - sammark[lower_index])) * (total_score - sammark[lower_index])
    
    return round(rank)

@login_required
def results_view(request):
    user_input = request.session.get('user_input', None)

    if user_input:
        predicted_rank = user_input['predicted_rank']
        preferred_college_id = user_input['preferred_college']
        preferred_branch_id = int(user_input['branch'])
        college_type = user_input['college_type']

        admission_message = "Less chance of getting into preferred college."

        if preferred_college_id and preferred_branch_id:
            preferred_college_id_int = int(user_input['preferred_college'])

            rank_response = supabase \
                .table('rankdetails') \
                .select('closing_rank') \
                .eq('college_id', preferred_college_id_int) \
                .eq('branch_id', preferred_branch_id) \
                .eq('year', 2019) \
                .execute()

            closing_rank_data = rank_response.data[0] if rank_response.data else None

            if closing_rank_data:
                closing_rank = closing_rank_data['closing_rank']
                if closing_rank is not None and predicted_rank <= closing_rank:
                    admission_message = "High chance of getting into preferred college and branch."
                else:
                    admission_message = "Less chance of getting into preferred college."

        elif not preferred_college_id:
            admission_message = "No preferred college selected. Please choose a college to check chances of admission."

        rank_details_response = supabase \
            .from_("rank_college_details") \
            .select("college_id, closing_rank, branch_id, year, type, category, college_name") \
            .eq("branch_id", preferred_branch_id) \
            .eq('type', college_type) \
            .gte("closing_rank", predicted_rank) \
            .eq('category', 'SM') \
            .eq('year', 2019) \
            .execute()

        top_colleges = []
        for detail in rank_details_response.data:
            if 'college_name' in detail:  
                top_colleges.append({
                    'college_name': detail['college_name'],
                    'closing_rank': detail['closing_rank']
                })

        top_colleges = sorted(top_colleges, key=lambda x: x['closing_rank'])[:10]

        return render(request, 'predictor/results.html', {
            'user_input': user_input,
            'top_colleges': top_colleges,
            'predicted_rank': predicted_rank,
            'admission_message': admission_message  
        })

    return redirect('predict')


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('predict_form')  
    else:
        form = UserCreationForm()
    return render(request, 'predictor/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('predict_form')  
    else:
        form = AuthenticationForm()
    return render(request, 'predictor/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')  