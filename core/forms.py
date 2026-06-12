from .validators import validate_github_url


class GitHubURLValidationMixin:
    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url", ""))
