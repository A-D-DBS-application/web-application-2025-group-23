class Config:
    SECRET_KEY = 'your_secret_key'
    
    SQLALCHEMY_DATABASE_URI = (
        'postgresql://postgres.flijuodhzqnqvabpgqpj:Barter.com123%21'
        '@aws-1-us-east-1.pooler.supabase.com:5432/postgres'
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #de %21 is voor het ! teken in de wachtwoord
    #code supabase = Barter.com123!
