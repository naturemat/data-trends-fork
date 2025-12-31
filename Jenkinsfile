pipeline {
    agent any

    stages {
        stage('Preparar Entorno') {
            steps {
                echo '--- 1. Instalando Dependencias ---'
                // Ajustamos requisitos y librerias
                sh "sed -i 's/Flask-CORS==3.1.1/Flask-CORS/' requirements.txt"
                sh "sed -i 's/openai==0.4.6/openai/' requirements.txt"
                sh 'sudo pip3 install --upgrade pyOpenSSL'
                
                // Instalamos todo lo necesario (incluyendo gunicorn)
                sh 'sudo pip3 install -r requirements.txt'
                sh 'sudo pip3 install pandas pytest mongomock gunicorn'
            }
        }

        stage('Configurar Secretos') {
            steps {
                echo '--- 2. Creando archivo .env temporal para tests ---'
                // OJO: Estas variables son SOLO para que pasen los tests dentro de Jenkins
                sh '''
                    echo "MONGODB_URL=mongodb://Grupo1:passGrupo1@3.151.181.99:27017/scraper_db?authSource=admin" > .env
                    echo "FLASK_ENV=production" >> .env
                    echo "GROQCLOUD_API_KEY=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" >> .env
                '''
            }
        }

        stage('QA - Tests Automáticos') {
            steps {
                echo '--- 3. Ejecutando Pruebas de Calidad (Pytest) ---'
                sh 'pytest tests/ --verbose'
            }
        }

        stage('🚀 Despliegue (CD)') {
            steps {
                echo '--- 4. Desplegando a Producción ---'
                
                // AQUI ESTA LA MAGIA DEL CD:
                // 1. Copiamos los archivos aprobados a la carpeta real del servidor
                sh 'rsync -av --exclude=".git" --exclude="venv" --exclude="__pycache__" . /var/www/scraper/'
                
                // 2. Reiniciamos el servicio que configuraste por SSH
                sh 'sudo systemctl restart scraper'
            }
        }
    }
    
    post {
        always {
            cleanWs()
            echo '♻️ Workspace limpiado.'
        }
        success {
            echo '🎉 ¡DESPLIEGUE EXITOSO! Tu app se actualizó sola.'
        }
    }
}