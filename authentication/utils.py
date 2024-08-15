from django.core.mail import send_mail


SENDER_EMAIL = 'hargetdev@gmail.com'


def send_register_email(username, email):
    subject = 'NartSozluk Kaydınız başarıyla gerçekleşti'
    message = """
    NartSozluk'e hoş geldiniz!
    \n
    Sizleri aramızda görmek çok güzel, topluluk kurallarına uyarak
    toplu bilgi birikimimize yapacağınız katkı için şimdiden
    teşekkür ederiz!
    \n
    Tekrardan hoş geldiniz {}!
    """.format(username)
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=SENDER_EMAIL,
            recipient_list=[email]
        )
        print("email sent to: ", email)
    except Exception as e:
        print("Error sending email: ", e)


def send_delete_account_email(username, email):
    subject = 'NartSozluk hesap silme işleminiz başarıyla gerçekleşti!'
    message = """
    NartSozluk'e veda ettiniz!
    \n
    Sözlüğe yaptığınız katkılar için teşekkür ederiz, her zaman
    gönlümüzde kalacaksınız. Sakın korkmayın verilerinizi sildik
    yazdığını entry'leri ise silinmiş kullanıcı adıyla göstermeye
    devam etmekteyiz.
    \n
    Tekrardan elveda {}!
    """.format(username)
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=SENDER_EMAIL,
            recipient_list=[email]
        )
        print("email sent to: ", email)
    except Exception as e:
        print("Error sending email: ", e)
