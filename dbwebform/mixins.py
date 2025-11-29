from markupsafe import Markup


class DjangoStyleFormMixin:
    def as_p(self, include_hidden_fields: bool = True):
        """Рендерит форму как последовательность тегов <p>"""
        html = []
        for field in self:
            if not include_hidden_fields and field.type in ['HiddenField', 'CSRFTokenField']:
                continue

            if field.type in ['HiddenField', 'CSRFTokenField']:
                html.append(str(field))
            else:
                # Основной field
                field_html = []

                # Label
                field_html.append(f'{field.label}')

                # Input field
                field_html.append(str(field))

                # Help text
                if hasattr(field, 'help_text') and field.help_text:
                    field_html.append(f'<span class="helptext">{field.help_text}</span>')

                # Errors
                if field.errors:
                    error_html = ['<ul class="errorlist">']
                    for error in field.errors:
                        error_html.append(f'<li>{error}</li>')
                    error_html.append('</ul>')
                    field_html.append(''.join(error_html))

                html.append(f'<p>{" ".join(field_html)}</p>')

        return Markup(''.join(html))