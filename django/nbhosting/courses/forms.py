from django import forms
from django.forms import ModelForm

from .model_course import CourseDir

class CourseForm(ModelForm):

    required_css_class = 'required'

    class Meta:
        model = CourseDir
        fields = ['autopull']

class UpdateCourseForm(forms.Form):
    autopull = forms.BooleanField(
        required=False,
        help_text=("when enabled, will automatically "
                   "pull every hour from your git remote"),
        )

    def clean_autopull(self):
        """
        fake validator - not too useful for that field but just to keep track
        https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Forms
        """
        data = self.cleaned_data['autopull']

        if data in (True, False):
            return data
        return False
