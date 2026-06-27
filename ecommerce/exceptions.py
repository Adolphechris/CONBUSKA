"""
Exceptions métier pour le module e-commerce.

Ces exceptions sont levées par les services de synchronisation
et d'import pour signaler des erreurs spécifiques.
"""


class EcommerceException(Exception):
    """Exception de base pour le module e-commerce."""
    pass


class FirebaseConnectionError(EcommerceException):
    """Erreur de connexion à Firebase."""
    pass


class ArticleNonPublieError(EcommerceException):
    """Article non publié, ne peut pas être synchronisé."""
    pass


class StockInsuffisantError(EcommerceException):
    """Stock insuffisant pour honorer la commande."""
    pass


class ArticleInexistantError(EcommerceException):
    """Article n'existe pas dans Conbuska."""
    pass


class PrixIncoherentError(EcommerceException):
    """Prix dans la commande ne correspond pas au prix actuel."""
    pass


class CommandeDejaImporteeError(EcommerceException):
    """Commande déjà importée (doublon)."""
    pass


class ImageTransformationError(EcommerceException):
    """Erreur lors de la transformation d'une image."""
    pass


class SyncError(EcommerceException):
    """Erreur générique de synchronisation."""
    pass