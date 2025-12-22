pipeline {
    agent any

    // (Eliminé el bloque environment vacío que causaba el error)

    stages {
        stage('Preparar Entorno') {
            steps {
                echo '--- 1. Instalando Dependencias y Arreglando Librerías ---'
                // TUS CORRECCIONES ORIGINALES
                sh "sed -i 's/Flask-CORS==3.1.1/Flask-CORS/' requirements.txt"
                sh "sed -i 's/openai==0.4.6/openai/' requirements.txt"
                sh 'sudo pip3 install --upgrade pyOpenSSL'
                
                // Instalación de dependencias + Pytest
                sh 'sudo pip3 install -r requirements.txt'
                sh 'sudo pip3 install pandas pytest mongomock'
            }
        }

        stage('Configurar Secretos') {
            steps {
                echo '--- 2. Creando archivo .env temporal ---'
                // Creamos el archivo .env real que necesita Python para leer las claves
                sh '''
                    echo "MONGODB_URL=mongodb://Grupo1:passGrupo1@3.151.181.99:27017/scraper_db?authSource=admin" > .env
                    echo "FLASK_ENV=production" >> .env
                    echo "SECRET_KEY=clave_secreta_jenkins" >> .env
                    echo "GROQCLOUD_API_KEY=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" >> .env
                    echo "OPENAI_API_KEY=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" >> .env
                '''
            }
        }

        stage('QA - Tests Automáticos') {
            steps {
                echo '--- 3. Ejecutando Pruebas de Calidad (Pytest) ---'
                // Ejecutamos los tests. Si fallan, el pipeline se detiene aquí.
                sh 'pytest tests/ --verbose'
            }
        }
    }
    
    post {
        always {
            // Limpieza al final
            cleanWs()
            echo '♻️ Entorno limpiado.'
        }
        success {
            echo '✅ ¡QA APROBADO! El código es seguro para subir a producción.'
        }
        failure {
            echo '❌ QA FALLIDO. Revisa los errores en la consola.'
        }
    }
}