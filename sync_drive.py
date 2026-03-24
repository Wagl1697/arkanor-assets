import os
import io
import hashlib
import shutil
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

ROOT_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID')
LOCAL_ROOT_DIR = 'img'

# Acá vamos a anotar todas las rutas exactas que SÍ existen en tu Drive hoy
archivos_validos = set()

def get_local_md5(file_path):
    if not os.path.exists(file_path):
        return None
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_folder(service, folder_id, local_path):
    if not os.path.exists(local_path):
        os.makedirs(local_path)

    # Anotamos esta carpeta como válida
    archivos_validos.add(os.path.abspath(local_path))

    query = f"'{folder_id}' in parents and trashed = false and (mimeType contains 'image/' or mimeType = 'application/vnd.google-apps.folder')"
    page_token = None
    
    while True:
        results = service.files().list(
            q=query, 
            spaces='drive',
            fields="nextPageToken, files(id, name, mimeType, md5Checksum)",
            pageToken=page_token
        ).execute()
        
        items = results.get('files', [])
        
        for item in items:
            item_id = item['id']
            item_name = item['name']
            mime_type = item['mimeType']
            drive_md5 = item.get('md5Checksum') 
            
            item_local_path = os.path.join(local_path, item_name)

            if mime_type == 'application/vnd.google-apps.folder':
                print(f"📁 Entrando a la subcarpeta: {item_local_path}")
                download_folder(service, item_id, item_local_path)
            elif mime_type.startswith('image/'):
                
                # Anotamos esta imagen como válida
                archivos_validos.add(os.path.abspath(item_local_path))
                
                local_md5 = get_local_md5(item_local_path)
                if local_md5 and drive_md5 and local_md5 == drive_md5:
                    print(f"  ✅ Omitiendo {item_name} (Sin cambios)")
                    continue

                print(f"  ⬇️ Descargando imagen: {item_name}...")
                request = service.files().get_media(fileId=item_id)
                fh = io.FileIO(item_local_path, 'wb')
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
            else:
                print(f"  ⏭️ Ignorando archivo (no es imagen): {item_name}")
                
        page_token = results.get('nextPageToken', None)
        if page_token is None:
            break

def clean_orphan_files(local_root):
    print("\n🧹 Iniciando limpieza de archivos huérfanos...")
    
    # Recorremos de abajo hacia arriba (topdown=False) para borrar archivos primero y luego vaciar carpetas
    for root, dirs, files in os.walk(local_root, topdown=False):
        for name in files:
            file_path = os.path.abspath(os.path.join(root, name))
            if file_path not in archivos_validos:
                os.remove(file_path)
                print(f"  🗑️ Archivo eliminado: {file_path}")
        
        for name in dirs:
            dir_path = os.path.abspath(os.path.join(root, name))
            if dir_path not in archivos_validos:
                shutil.rmtree(dir_path)
                print(f"  🗑️ Carpeta eliminada: {dir_path}")

def main():
    print("Iniciando autenticación con Google Cloud...")
    credentials, project = google.auth.default()
    service = build('drive', 'v3', credentials=credentials)
    
    if not ROOT_FOLDER_ID:
        print("❌ Error: No se encontró el DRIVE_FOLDER_ID en los secretos.")
        return

    print("Empezando la sincronización desde Drive...")
    
    # 1. Traemos lo nuevo y anotamos lo que existe
    download_folder(service, ROOT_FOLDER_ID, LOCAL_ROOT_DIR)
    
    # 2. Pasamos la escoba a lo que ya no está en Drive
    clean_orphan_files(LOCAL_ROOT_DIR)
    
    print("\n✅ ¡Sincronización finalizada con éxito!")

if __name__ == '__main__':
    main()
