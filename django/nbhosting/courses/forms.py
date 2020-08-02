# pylint: disable=c0111
from django import forms
from django.forms import ModelForm

from .model_course import CourseDir

class CourseForm(ModelForm):

    required_css_class = 'required'

    class Meta:
        model = CourseDir
        fields = ['autopull', 'archived', 'image', 'staff_usernames']

class UpdateCourseForm(forms.Form):
    autopull = forms.BooleanField(
        label='autopull',
        required=False,
        help_text=("when enabled, will automatically "
                   "pull every hour from your git remote"),
        )
    archived = forms.BooleanField(
        label='archived',
        required=False,
        help_text=("archived courses do not show up in the default courses list"),
        )
    image = forms.CharField(
        label='image',
        required=False,
        help_text="""
            the name of the container image used to spawn student containers for
            that course; you have the option to use one of the built-in
            nbhosting images  <code>nbhosting/minimal-notebook</code> and
            <code>nbhosting/scipy-notebook</code>; or, you may just refer to the
            name of an image defined by another course on that nbhosting
            instance; or, you can leave this setting to be your course's name,
            in which case you are supposed to provide a
            <code>nbhosting/Dockerfile</code> as part of your git repo; in the
            latter case you will be responsible for triggering rebuilds of that
            image""",
        )
    staff_usernames = forms.CharField(
        label='staff_usernames',
        required=False,
        strip=True,
        widget=forms.Textarea(attrs={
            'rows': 10,
            'cols': 100,
        }),
        help_text="""
        the names of users that are considered staff for this course;
        this is mainly used to ignore activity from these people
        when computing statistics
        """
    )

#    def clean_autopull(self):
#        """
#        fake validator - not too useful for that field but just to keep track
#        https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Forms
#        """
#        data = self.cleaned_data['autopull']
#
#        if data in (True, False):
#        return False
