document.addEventListener('DOMContentLoaded', () => {

    // Use buttons to toggle between views
    document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
    document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
    document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
    document.querySelector('#compose').addEventListener('click', compose_email);

    document.querySelector('#compose-form').addEventListener('submit', send_email);

    // By default, load the inbox
    load_mailbox('inbox');
});

function archive(email, block, location) {

    const button = document.createElement('button');
    button.classList.add('btn', 'btn-sm', 'btn-outline-primary');
    button.innerHTML = (location === 'inbox') ? 'Archive' : 'Unarchive';
    block.append(button);

    button.addEventListener('click', () => {
        fetch(`emails/${email.id}`, {
            method: 'PUT',
            body: JSON.stringify({
                archived: !email.archived
            })
        })
        .then(() => load_mailbox('inbox'));
    });
}

function compose_email() {

    document.querySelector('#compose-error').style.display = 'none';

    // Show compose view and hide other views
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#email-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'block';

    // Clear out composition fields
    document.querySelector('#compose-recipients').value = '';
    document.querySelector('#compose-subject').value = '';
    document.querySelector('#compose-body').value = '';
}

function load_mailbox(mailbox) {

    fetch(`/emails/${mailbox}`)
    .then(response => response.json())
    .then(emails => {
        console.log(emails);

        if (emails.length === 0) {
            const heading = document.createElement('p');
            heading.innerHTML = 'No emails yet.';
            document.querySelector('#emails-view').append(heading);
            return;
        }
        if ('error' in emails) { return; }

        emails.forEach(email => {
            const email_box = document.createElement('div');
            subject = (email.subject) ? email.subject : '(no subject)';
            email_box.innerHTML = `<strong>${email.sender}</strong> ${subject} ${email.timestamp}`;
            email_box.classList.add('email');
            (email.read) ? email_box.classList.add('read') : email_box.classList.add('unread');
            document.querySelector('#emails-view').append(email_box);

            email_box.addEventListener('click', () => view_email(email.id));
        });
    });

    // Show the mailbox and hide other views
    document.querySelector('#emails-view').style.display = 'block';
    document.querySelector('#email-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'none';

    // Show the mailbox name
    document.querySelector('#emails-view').innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;
}

function reply_email(recipient, subject, body) {

    document.querySelector('#compose-error').style.display = 'none';

    // Show compose view and hide other views
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#email-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'block';

    // Clear out composition fields
    document.querySelector('#compose-recipients').value = recipient;
    document.querySelector('#compose-subject').value = subject;
    document.querySelector('#compose-body').value = body;
}

function send_email(event) {

    const error_message = document.querySelector('#compose-error');

    fetch('/emails', {
        method: 'POST',
        body: JSON.stringify({
            recipients: document.querySelector('#compose-recipients').value,
            subject: document.querySelector('#compose-subject').value,
            body: document.querySelector('#compose-body').value
        })
    })
    .then(response => response.json())
    .then(result => {
        if ('error' in result) {
            compose_email();
            error_message.innerHTML = result.error;
            error_message.style.display = 'block';
        } else {
            error_message.innerHTML = '';
            load_mailbox('sent');
        }
    });
    event.preventDefault();
}

function view_email(email_id) {

    let email_block = document.querySelector('#email-view');

    fetch(`/emails/${email_id}`)
    .then(response => response.json())
    .then(email => {
        email_block.innerHTML = `<p><strong>From: </strong>${email.sender}</p><p><strong>To: </strong>${email.recipients}</p><p><strong>Subject: </strong>${email.subject}</p><p><strong>Timestamp: </strong>${email.timestamp}</p><p>${email.body}</p>`;

        const button = document.createElement('button');
        button.classList.add('btn', 'btn-sm', 'btn-outline-primary');
        button.innerHTML = 'Reply';
        email_block.append(button);

        button.addEventListener('click', () => reply_email(
            email.sender, 
            (email.subject.startsWith('Re: ')) ? email.subject : `Re: ${email.subject}`,
            `On ${email.timestamp} ${email.sender} wrote: ${email.body}`
        ));

        if (!email.read) {
            fetch(`/emails/${email_id}`, {
                method: 'PUT',
                body: JSON.stringify({
                    read: true
                })
            });
        }

        if (email.archived) {
            archive(email, email_block, 'archive');
        } else {
            fetch('/emails/inbox')
            .then(response => response.json())
            .then(emails => {
                emails.some(function(inboxEmail) {
                    if (inboxEmail.id === email.id) {
                        archive(email, email_block, 'inbox');
                        return true;
                    }
                });
            });
        }
    });

    // Show the email and hide other views
    email_block.style.display = 'block';
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'none';
}
