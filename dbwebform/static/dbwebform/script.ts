declare function input_form_control_unline(form: HTMLFormElement): void

const form: HTMLFormElement | null = document.querySelector('.form')

if (form)
    input_form_control_unline(form)

