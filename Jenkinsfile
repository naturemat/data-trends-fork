pipeline {
    agent any

    environment {
        MONGODB_URL = credentials('MONGO_URL')
    }

    stages {
        stage('Preparar Entorno') {
            steps {
                echo '--- 1. Instalando Dependencias (Test) ---'
                // Ajustes de versiones en requirements.txt
                sh "sed -i 's/Flask-CORS==3.1.1/Flask-CORS/' requirements.txt"
                sh "sed -i 's/openai==0.4.6/openai/' requirements.txt"
                
                // --- CAMBIO AQUÍ: Eliminé la línea de pyOpenSSL que daba error ---
                
                // Instalamos las dependencias del proyecto
                // Agregamos --ignore-installed por seguridad si hay conflictos futuros
                sh 'sudo pip3 install -r requirements.txt --break-system-packages --ignore-installed'
                sh 'sudo pip3 install pandas pytest mongomock gunicorn --break-system-packages --ignore-installed'
            }
        }

        stage('QA - Tests Automáticos') {
            steps {
                echo '--- 2. Ejecutando Pruebas de Calidad (Pytest) ---'
                sh 'pytest tests/ --verbose'
            }
        }

        stage('🚀 Despliegue Remoto (CD)') {
            steps {
                script {
                    // DATOS DE CONEXIÓN A LA INSTANCIA A (PRODUCCIÓN)
                    def prodIP = "172.31.39.188"
                    def remoteUser = "ubuntu"
                    def targetDir = "/var/www/scraper/"

                    echo "--- 3. Desplegando a Producción (${prodIP}) ---"

                    // A. Generamos el archivo .env
                    sh """
                        echo "MONGODB_URL=${MONGODB_URL}" > .env
                        echo "FLASK_ENV=production" >> .env
                        echo "API_BASE_URL=http://3.151.181.99:5000" >> .env
                        echo "GROQCLOUD_API_KEY=***REMOVED***" >> .env
                    """

                    // B. Enviamos los archivos a la OTRA máquina
                    sh """
                        rsync -avz -e "ssh -o StrictHostKeyChecking=no" \
                        --exclude='.git' \
                        --exclude='venv' \
                        --exclude='__pycache__' \
                        --exclude='tests' \
                        ./ ${remoteUser}@${prodIP}:${targetDir}
                    """

                    // C. Reiniciamos el servicio en la OTRA máquina
                    sh """
                        ssh -o StrictHostKeyChecking=no ${remoteUser}@${prodIP} \
                        'sudo systemctl restart scraper'
                    """
                }
            }
        }
    }

    post {
        always {
            cleanWs()
            echo '♻️ Workspace limpiado.'
        }
        success {
            echo '🎉 ¡DESPLIEGUE EXITOSO! La Instancia A ha sido actualizada.'
        }
        failure {
            echo '❌ El pipeline falló. Revisa los logs.'
        }
    }
}