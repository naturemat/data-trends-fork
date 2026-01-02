pipeline {
    agent any

    stages {

        stage('Preparar Entorno') {
            steps {
                echo '--- 1. Instalando Dependencias ---'
                sh "sed -i 's/Flask-CORS==3.1.1/Flask-CORS/' requirements.txt"
                sh "sed -i 's/openai==0.4.6/openai/' requirements.txt"
                sh 'sudo pip3 install --upgrade pyOpenSSL'
                sh 'sudo pip3 install -r requirements.txt'
                sh 'sudo pip3 install pandas pytest mongomock gunicorn'
            }
        }

        stage('Configurar Secretos') {
            steps {
                echo '--- 2. Creando archivo .env final para Producción ---'
                sh '''
                    echo "MONGODB_URL=mongodb://Grupo1:passGrupo1@3.151.181.99:27017/scraper_db?authSource=admin" > .env
                    echo "FLASK_ENV=production" >> .env
                    echo "API_BASE_URL=http://3.151.181.99:5000" >> .env
                    echo "GROQCLOUD_API_KEY=***REMOVED***" >> .env
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

                // Asegurar que la carpeta existe y Jenkins puede escribir
                sh '''
                    sudo mkdir -p /var/www/scraper
                    sudo chown -R jenkins:jenkins /var/www/scraper
                '''

                // Copiamos el código y el .env a producción
                sh '''
                    sudo rsync -av \
                      --exclude=".git" \
                      --exclude="venv" \
                      --exclude="__pycache__" \
                      . /var/www/scraper/
                '''

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
        failure {
            echo '❌ El pipeline falló. Revisa los logs.'
        }
    }
}
