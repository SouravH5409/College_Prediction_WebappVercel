from django import forms
from .utils import get_college_choices, get_branch_choices

class UserInputForm(forms.Form):
    BOARD_CHOICES = [
        (None, 'Select an option'),
        ('CBSE', 'CBSE'),
        ('ICSE', 'ICSE'),
        ('STATE', 'State Board'),
    ]
    
    COLLEGE_TYPE_CHOICES = [
        (None, 'Select College Type'),
        ('G', 'Government'),
        ('S', 'Self-Financed'),
        ('N', 'College Run by Government Institution'),
    ]

    board = forms.ChoiceField(choices=BOARD_CHOICES, required=True)
    physics_marks = forms.IntegerField(required=True, min_value=0, help_text="Enter marks for Physics")
    chemistry_marks = forms.IntegerField(required=True, min_value=0, help_text="Enter marks for Chemistry")
    maths_marks = forms.IntegerField(required=True, min_value=0, help_text="Enter marks for Maths")
    keam_score = forms.IntegerField(required=True)    
    preferred_branch = forms.ChoiceField(choices=get_branch_choices(), required=True)
    college_type = forms.ChoiceField(choices=COLLEGE_TYPE_CHOICES, required=True)
    preferred_college = forms.ChoiceField(choices=get_college_choices(), required=False, help_text="Select the preferred college (if any)")

    def clean(self):
        cleaned_data = super().clean()
        board = cleaned_data.get('board')
        physics_marks = cleaned_data.get('physics_marks')
        chemistry_marks = cleaned_data.get('chemistry_marks')
        maths_marks = cleaned_data.get('maths_marks')
        keam_score = cleaned_data.get('keam_score') 

        if keam_score is not None and keam_score < 20:
            self.add_error('keam_score', 'KEAM eligibility requires a minimum score of 20 (10 in each paper).')

        if board in ['CBSE', 'ICSE']:
            if (physics_marks > 100 or chemistry_marks > 100 or maths_marks > 100):
                self.add_error('physics_marks', 'Marks for each subject should be out of 100 for CBSE/ICSE.')
                self.add_error('chemistry_marks', 'Marks for each subject should be out of 100 for CBSE/ICSE.')
                self.add_error('maths_marks', 'Marks for each subject should be out of 100 for CBSE/ICSE.')
            else:
                if ((physics_marks + chemistry_marks)/2) < 45:
                    self.add_error('physics_marks', r'Average of Physics and Chemistry must be 45% or more.')
                    self.add_error('chemistry_marks', r'Average of Physics and Chemistry must be 45% or more.')
                if maths_marks < 45:
                    self.add_error('maths_marks', 'Maths marks must be at least 45%.')

        elif board == 'STATE':
            if (physics_marks > 120 or chemistry_marks > 120 or maths_marks > 100):
                self.add_error('physics_marks', 'Marks for Physics should be out of 120 for State Board.')
                self.add_error('chemistry_marks', 'Marks for Chemistry should be out of 120 for State Board.')
                self.add_error('maths_marks', 'Marks for Maths should be out of 100 for State Board.')
            else:
                if ((physics_marks + chemistry_marks)/240*100) < 45:
                    self.add_error('physics_marks', r'Average of Physics and Chemistry must be 45% or more.')
                    self.add_error('chemistry_marks', r'Average of Physics and Chemistry must be 45% or more.')
                if maths_marks < 45:
                    self.add_error('maths_marks', 'Maths marks must be at least 45%.')    

        return cleaned_data
