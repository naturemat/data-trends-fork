pipeline {
    agent any

    environment {
        MONGODB_URL = credentials('MONGO_URL')
    }

    stages {
        stage('Preparar Entorno') {
            steps {
                echo '--- 1. Instalando Dependencias (Test) ---'
                sh "sed -i 's/Flask-CORS==3.1.1/Flask-CORS/' requirements.txt"
                sh "sed -i 's/openai==0.4.6/openai/' requirements.txt"
                
                // 1. Instalamos las librerías pesadas (PyTorch CPU)
                sh '''
                    sudo pip3 install -r requirements.txt \
                    --index-url https://download.pytorch.org/whl/cpu \
                    --extra-index-url https://pypi.org/simple \
                    --break-system-packages \
                    --ignore-installed \
                    --no-cache-dir
                '''
                
                // 2. Instalamos las herramientas de test manualmente
                sh 'sudo pip3 install pytest mongomock gunicorn python-dotenv --break-system-packages --ignore-installed --no-cache-dir'
            }
        }

        stage('QA - Tests Automáticos') {
            steps {
                echo '--- 2. Ejecutando Pruebas de Calidad (Pytest) ---'
                
                // CORRECCIÓN FINAL:
                // Usamos 'env' para pasar la variable OPENAI_API_KEY falsa.
                // Esto engaña a la aplicación para que arranque sin pedir la llave real.
                sh 'sudo env PYTHONPATH=. OPENAI_API_KEY=sk-proj-dummy-key-para-tests python3 -m pytest tests/ --verbose'
            }
        }

        stage('🚀 Despliegue Remoto (CD)') {
            steps {
                script {
                    def prodIP = "172.31.39.188"
                    def remoteUser = "ubuntu"
                    def targetDir = "/var/www/scraper/"

                    echo "--- 3. Desplegando a Producción (${prodIP}) ---"

                    sh """
                        echo "MONGODB_URL=${MONGODB_URL}" > .env
                        echo "FLASK_ENV=production" >> .env
                        echo "API_BASE_URL=http://3.151.181.99:5000" >> .env
                        echo "GROQCLOUD_API_KEY=***REMOVED***" >> .env
                    """

                    sh """
                        rsync -avz -e "ssh -o StrictHostKeyChecking=no" \
                        --exclude='.git' \
                        --exclude='venv' \
                        --exclude='__pycache__' \
                        --exclude='tests' \
                        ./ ${remoteUser}@${prodIP}:${targetDir}
                    """

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