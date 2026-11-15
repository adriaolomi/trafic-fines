import pathlib

CACHE_DIR = Path.home() / ".my_cache"

class Cache:
    
    def __init__(self, app_name, obsolence) -> None:
        """
        app_name, un str que será un nombre asociado a la aplicación concreta. Este atributo se usará para crear una subcarpeta dentro de la carpeta CACHE_DIR. De esta forma, cada aplicación tendrá una carpeta dentro de CACHE_DIR para almacenar sus datos.
        cache_dir, un string con la ruta completa de la subcarpeta que usará la aplicación para almacenar sus datos.
        obsolescence, un int que indica el número de días que consideraremos que los datos de la caché siguen siendo válidos.
        """
        self.__app_name: str,
        self.__cache_dir: str,
        self.__obsolescence: int
        
    def set(self, name:str, data:str) -> None : 
        """
        método que almacena en cache_dir los datos en data con el nombre name.
        """
            
    def exists(self, name: str) -> bool :
        """
        Comprueba si ya existe un fichero con el nombre name en la caché cache_dir.
        """
        
    def load(self, name: str) -> str: 
        """
        método que recupera los datos almacenados en la caché, con el nombre name. Si no hay ningún dato asociado deberá lanzar la excepción CacheError.
        """
        
    def how_old(self, name: str) -> float: 
        """
        método que nos dirá la edad en milisegundos del fichero almacenado en la caché con el nombre indicado. Esto sirve para     comprobar si el fichero está caducado según el valor de obsolescence.
        """
            
    def delete(self, name: str) -> None: 
        """
        método que borra de la caché el fichero con nombre nane. Si no existe, no se lanza ninguna excepción.
        """
        
    def clear(self) -> None: 
        """
        método que borra todos los elementos de la caché.
        """

    def __str__(self): 
        text = "AppName: " + self.__app_name + "CacheDir: " \+ self.cache_dir + 'Obsolescence: ' + self.__obsolescence
        return text

        

class CacheURL(Cache):

    def __init__ (self, app_name, obsolence,)
        super().__init__(app_name, obsolence)

    def get(self, url:str) -> str 
        """
        Este método va a realizar un get a la url indicada. Este método consultará si tiene ya un objeto asociado a esta petición,
        si no lo tiene realizará la petición correspondiente, guardará el resultado en la caché. Devolverá el objeto
        correspondiente.
        """

    # Redefinir    
    def exists(self, url: str, **kwargs) -> bool
    
    def load(self, url: str, **kwargs) -> str
    
    def how_old(self, name: str, **kwargs) -> float
    
    def delete(self, name: str, **kwargs) -> None

    def __str__(self):
        text = super().__str__()
        return text
