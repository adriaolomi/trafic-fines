from pathlib import Path
import shutil
import time
import hashlib

CACHE_DIR = Path.home() / ".my_cache"

class Cache:
    
    def __init__(self, app_name, obsolescence) -> None:
        """
        app_name, un str que será un nombre asociado a la aplicación concreta. Este atributo se usará para crear una subcarpeta dentro de la carpeta CACHE_DIR. De esta forma, cada aplicación tendrá una carpeta dentro de CACHE_DIR para almacenar sus datos.
        cache_dir, un string con la ruta completa de la subcarpeta que usará la aplicación para almacenar sus datos.
        obsolescence, un int que indica el número de días que consideraremos que los datos de la caché siguen siendo válidos.
        """
        self.__app_name = app_name
        self.__cache_dir = CACHE_DIR / app_name
        self.__obsolescence = obsolescence

    
    @property
    def app_name(self)-> str:          # getter
        return self.__app_name 
        
    @property
    def cache_dir(self)-> str:         # getter
        return self.__cache_dir

    @property
    def obsolescence(self)-> int:      # getter
        return self.__obsolescence 


    # FET
    def set(self, name:str, data:str) -> None : 
        """
        Método que almacena en cache_dir los datos en data con el nombre name.

        :param a: El primer número entero.
        :param b: El segundo número entero.
    
        :returns a: El máximo común divisor de `a` y `b`.
        """
        # Crear los directorios de cache, si no existen previamente
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Escribir en fichero
        with open(self.cache_dir / name, 'w') as f:
            f.write(data)

            
    def exists(self, name: str) -> bool :
        """
        Comprueba si ya existe un fichero con el nombre name en la caché cache_dir.
        """
        full_path = self.cache_dir / name
        if full_path.exists():
            return True
        else:
            return False

        
    def load(self, name: str) -> str: 
        """
        método que recupera los datos almacenados en la caché, con el nombre name. 
        Si no hay ningún dato asociado deberá lanzar la excepción CacheError.
        
        :param name: string que representa únicamente el nombre del fichero, no el path completo.
        
        :raises CacheError: Si el archivo no existe en la caché
        """
        if self.exists(name):
            file = open(self.cache_dir / name)
            lines = file.readlines()
            return lines
        else:
            raise CacheError(f"El archivo {name} no existe en la cache!")

        
    def how_old(self, name: str) -> float: 
        """
        método que nos dirá la edad en milisegundos del fichero almacenado en la caché con el nombre indicado. 
        Esto sirve para comprobar si el fichero está caducado según el valor de obsolescence.
        """
        full_path = self.cache_dir / name
        creation_time = full_path.stat().st_mtime
        current_time = time.time()
        age_seconds = current_time - creation_time
        return age_seconds * 1000

    
    def delete(self, name: str) -> None: 
        """
        método que borra de la caché el fichero con nombre name. Si no existe, no se lanza ninguna excepción.
        """
        # Si el fichero existe, se elimina
        full_path = self.cache_dir / name
        if self.exists(full_path):
            name.unlink()
        
    def clear(self) -> None: 
        """
        método que borra todos los elementos de la caché.
        """
        # Si el directorio existe, se elimina
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
    
    def __str__(self): 
        text = "AppName: " + self.app_name + " , CacheDir: " + str(self.cache_dir) + ' , Obsolescence: ' + str(self.obsolescence)
        return text

    
    def __repr__(self): 
        text = "AppName: " + self.app_name + " , CacheDir: " + str(self.cache_dir) + ' , Obsolescence: ' + str(self.obsolescence)
        return text

        
class CacheURL(Cache):

    def __init__ (self, app_name, obsolence):
        super().__init__(app_name, obsolence)

    
    def get(self, url:str) -> str:
        """
        Este método va a realizar un get a la url indicada. Este método consultará si tiene ya un objeto asociado a esta petición,
        si no lo tiene realizará la petición correspondiente, guardará el resultado en la caché. Devolverá el objeto
        correspondiente.
        """
        try:
            resp = requests.get(url,  timeout=15)
            if resp.status_code != 200:
                url_hashed = hashlib.md5(url.encode('utf-8')).hexdigest()
                url_hashed
                return None
        except requests.RequestException as e:
            print("Error de conexión:", e)
            return None

    # Redefinir    
    def exists(self, url: str, **kwargs) -> bool:
        return False

        
    def load(self, url: str, **kwargs) -> str:
        return "Hola"

        
    def how_old(self, name: str, **kwargs) -> float:
        return 1.0

        
    def delete(self, name: str, **kwargs) -> None:
        return 0

    
    def __str__(self):
        text = super().__str__()
        return text



## EXCEPCIONES ##
class CacheError(Exception):
    """Excepción lanzada por errores en la caché.

    Atributos:        
        message -- explicación del error
    """

    def __init__(self, message):
        self.message = message

    
######## MAIN ########
if __name__ == '__main__':
    c = Cache("olomi_test_dir", 12)
    print(str(c))

    c.set(name="olomi.txt", data="Hola, aixo es un test")
    print(c.load("olomi.txt"))

    print(c.how_old("olomi.txt"))