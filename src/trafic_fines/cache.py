from pathlib import Path
import shutil
import time
import hashlib
import requests
import io

CACHE_DIR = Path.home() / ".my_cache"

class Cache:
    
    def __init__(self, app_name, obsolescence) -> None:
        """
        Inicializa una caché asociada a una aplicación concreta.

        :param app_name: Nombre asociado a la aplicación. Este atributo se utilizará
                         para crear una subcarpeta dentro de CACHE_DIR.
        :type app_name: str
        :param obsolescence: Número de días durante los cuales los datos de la caché
                             se considerarán válidos.
        :type obsolescence: int
        """
        self.__app_name = app_name
        self.__cache_dir = CACHE_DIR / app_name
        self.__obsolescence = obsolescence

    
    @property
    def app_name(self)-> str:
        """
        Nombre asociado a la aplicación concreta. Este atributo se usará para crear una subcarpeta dentro de la carpeta CACHE_DIR. 
        De esta forma, cada aplicación tendrá una carpeta dentro de CACHE_DIR para almacenar sus datos.

        :return: Nombre de la aplicación.
        :rtype: str
        """
        return self.__app_name 
        
    @property
    def cache_dir(self)-> Path:
        """
        String con la ruta completa de la subcarpeta que usará la aplicación para almacenar sus datos.

        :return: Ruta del directorio de caché.
        :rtype: Path
        """
        return self.__cache_dir

    @property
    def obsolescence(self)-> int:
        """
        Indica el número de días que consideraremos que los datos de la caché siguen siendo válidos.

        :return: Número de días de obsolescencia.
        :rtype: int
        """
        return self.__obsolescence 


    def set(self, name:str, data:str) -> None:
        """
        Almacena en cache_dir los datos en data con el nombre name.

        :param name: Nombre del fichero donde se almacenarán los datos.
        :type name: str
        :param data: Datos que se desean almacenar en el fichero.
        :type data: str
        :return: No devuelve ningún valor.
        :rtype: None
        """
        # Crear los directorios de cache, si no existen previamente
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Escribir en fichero
        with open(self.cache_dir / name, 'w') as f:
            f.write(data)

            
    def exists(self, name: str) -> bool:
        """
        Comprueba si ya existe un fichero con el nombre indicado en el directorio de caché.

        :param name: Nombre del fichero que se desea comprobar.
        :type name: str
        :return: True si el fichero existe, False en caso contrario.
        :rtype: bool
        """
        full_path = self.cache_dir / name
        if full_path.is_file():
            return True
        else:
            return False

        
    def load(self, name: str) -> str:
        """
        Método que recupera los datos almacenados en la caché, con el nombre name. Si no hay ningún dato asociado deberá lanzar la excepción CacheError.

        :param name: Nombre del fichero que se desea recuperar. Debe representar únicamente el nombre del fichero, no la ruta completa.
        :type name: str
        :return: Datos almacenados en el fichero.
        :rtype: str
        :raises CacheError: Si el archivo no existe en la caché.
        """
        if self.exists(name):
            with open(self.cache_dir / name, 'r') as file:
                return file.read()
        else:
            raise CacheError(f"El archivo {name} no existe en la cache {self.app_name} con ruta {self.cache_dir}!")

        
    def how_old(self, name: str) -> float:
        """
        Método que nos dirá la edad en milisegundos del fichero almacenado en la caché con el nombre indicado. 
        Esto sirve para comprobar si el fichero está caducado según el valor de obsolescence

        :param name: Nombre del fichero cuya antigüedad se desea calcular.
        :type name: str
        :return: Antigüedad del fichero en milisegundos.
        :rtype: float
        """
        full_path = self.cache_dir / name
        creation_time = full_path.stat().st_mtime
        current_time = time.time()
        age_seconds = current_time - creation_time
        return age_seconds * 1000

    
    def delete(self, name: str) -> None:
        """
        Método que borra de la caché el fichero con nombre nane. Si no existe, no se lanza ninguna excepción.

        :param name: Nombre del fichero que se desea eliminar.
        :type name: str
        :return: No devuelve ningún valor.
        :rtype: None
        """
        # Si el fichero existe, se elimina
        full_path = self.cache_dir / name
        if full_path.is_file():
            full_path.unlink()
        
    def clear(self) -> None:
        """
        Método que borra todos los elementos de la caché.

        :return: No devuelve ningún valor.
        :rtype: None
        """
        # Si el directorio existe, se elimina
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
    
    def __str__(self):
        """
        Representación de la configuración de la caché.

        :return: Cadena con el nombre de la aplicación, la ruta del directorio
                 de caché y el periodo de obsolescencia.
        :rtype: str
        """
        text = "AppName: " + self.app_name + " , CacheDir: " + str(self.cache_dir) + ' , Obsolescence: ' + str(self.obsolescence)
        return text

        
class CacheURL(Cache):

    def __init__ (self, app_name, obsolescence):
        super().__init__(app_name, obsolescence)

    
    def get(self, url:str, **kwargs) -> str:
        """
        Este método va a realizar un get a la url indicada. Este método consultará si tiene ya un objeto asociado a esta petición,
        si no lo tiene realizará la petición correspondiente, guardará el resultado en la caché. Devolverá el objeto correspondiente.
        """

        # Si el objeto existe, lo devuelve
        if self.exists(url):
            return self.load(url)
        
        # Sino, lo descarga de internet
        else:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    url_hashed = hashlib.md5((url + str(kwargs)).encode('utf-8')).hexdigest()
                    super().set(name=url_hashed, data=response.text)
                    return self.load(url)
                else:
                    raise CacheError(
                        f"Error HTTP {response.status_code} al consultar {url}"
                    )
            except requests.RequestException as e:
                raise CacheError(f"Error de conexión con {url}: {e}") from e

    # Redefinición de la clase padre  
    def exists(self, url: str, **kwargs) -> bool:
        """
        Comprueba si ya existe un fichero con el nombre indicado en el directorio de caché.
        """
        url_hashed = hashlib.md5((url + str(kwargs)).encode('utf-8')).hexdigest()
        return super().exists(name=url_hashed)

    
    # Redefinición de la clase padre 
    def load(self, url: str, **kwargs) -> str:
        """
        Método que recupera los datos almacenados en la caché, con el nombre name. Si no hay ningún dato asociado deberá lanzar la excepción CacheError.
        """
        if self.exists(url):
            url_hashed = hashlib.md5((url + str(kwargs)).encode('utf-8')).hexdigest()   
            with open(self.cache_dir / url_hashed, 'r') as file:
                return file.read()
        else:
            raise CacheError(f"El archivo {url} no existe en la cache {self.app_name} con ruta {self.cache_dir}!")

    
    # Redefinición de la clase padre 
    def how_old(self, url: str, **kwargs) -> float:
        """
        Método que nos dirá la edad en milisegundos del fichero almacenado en la caché con el nombre indicado. 
        Esto sirve para comprobar si el fichero está caducado según el valor de obsolescence
        """
        url_hashed = hashlib.md5((url + str(kwargs)).encode('utf-8')).hexdigest()
        return super().how_old(name=url_hashed)
    

    # Redefinición de la clase padre   
    def delete(self, url: str, **kwargs) -> None:
        """
        Método que borra de la caché el fichero con nombre nane. Si no existe, no se lanza ninguna excepción.
        """
        url_hashed = hashlib.md5((url + str(kwargs)).encode('utf-8')).hexdigest()
        return super().delete(name=url_hashed)
    

    def __str__(self):
        """
        Representación de la configuración de la clase Caché URL.
        """
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

    
#################    MAIN     ####################
# No se incluye en el pytest -> # pragma: no cover
if __name__ == '__main__': # pragma: no cover

    ##
    c = CacheURL("olomi_url_test_dir", 12)
    print(str(c))

    raiz = "https://datos.madrid.es/"
    url_diciembre_24 = "dataset/210104-0-multas-circulacion-detalle/resource/210104-15-multas-circulacion-detalle-csv/download/210104-15-multas-circulacion-detalle-csv.csv" 
    url = raiz + url_diciembre_24.lstrip("/")
    c.get(url)

    print(c.how_old(url))