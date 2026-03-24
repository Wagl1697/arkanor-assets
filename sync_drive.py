- name: 💾 Guardar y subir cambios a GitHub
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          
          # ¡ESTA ES LA LÍNEA MÁGICA PARA LOS ACENTOS!
          git config --global core.quotepath off 
          
          # 1. Preparamos los cambios de la carpeta img
          git add img/
          
          # 2. Nos fijamos si Git detectó algún cambio
          if git diff --staged --quiet; then
            echo "No hay imágenes nuevas ni modificadas para subir. Terminando sin commit."
          else
            # 3. Si hay cambios, extraemos la lista exacta (A=Agregado, M=Modificado, D=Borrado)
            DETALLE=$(git diff --name-status --staged)
            
            # 4. Hacemos el commit armando un mensaje multilínea
            git commit -m "🖼️ Actualización automática de imágenes" -m "Detalle de los cambios:" -m "$DETALLE"
            
            # 5. Subimos los cambios a tu rama
            git push
            
            echo "✅ Commit realizado con el detalle de los cambios."
          fi
