"""
Module de synchronisation sortante Conbuska → Firestore.

Ce module contient les services de synchronisation des articles
vers la base de données Firestore de la boutique en ligne.
Il gère également l'upload et la transformation des images
vers Firebase Storage.

Modules :
- serializers.py : Transformation Article → document Firestore
- storage.py : Upload et transformation des images
- services.py : Logique métier de synchronisation
- tasks.py : Tâches planifiées (cron/Celery)
"""