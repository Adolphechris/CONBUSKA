
def is_duplicate(items: list, data: dict):
    """
    Cette methode verifie si les nouvelles donnees sont ou non dupliquees
        args:
            items: liste des entrees de l'entree de stock dans la base de donnees
            data: La nouvelle entree dont il faut verifier la duplication dans la liste
        returns:
            soit l'element similaire qui traduit la duplication, soit None s'il n'y a aucune correspondance
    """
    for i in items:
        if all(item in i.items() for item in data.items()):
            return i
    return None
