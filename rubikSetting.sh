# hostname: rubikpi
# passwd: rubikpi
# loginas(username): root
# ============================================
# Node.js 설치
# ============================================
# Node.js는 ARM64 아키텍처에 맞는 바이너리를 직접 다운로드하여 설치합니다.
# 이유: 패키지 관리자인 apt나 opkg를 사용하지 않는 환경이거나 최신 버전이 필요할 때
# wget으로 Node.js 바이너리를 다운로드한 후, 압축을 풀고 /usr/local/node에 설치합니다.
# 개발환경인 Windows 데스크탑 환경(Node.js v23.3.0, npm v10.9.0)에 맞춰 현재 실제 실행환경인 Rubik pi3의 환경을 구성.
echo "Installing Node.js..."
wget https://nodejs.org/dist/v23.3.0/node-v23.3.0-linux-arm64.tar.xz
tar -xf node-v23.3.0-linux-arm64.tar.xz
sudo mv node-v23.3.0-linux-arm64 /usr/local/node

# 환경 변수 설정: Node.js 실행 파일이 있는 경로를 PATH에 추가
echo 'export PATH=/usr/local/node/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# npm 최신 버전으로 업그레이드
echo "Upgrading npm to version 10.9.0..."
sudo npm install -g npm@10.9.0

# Node.js 및 npm 버전 확인
echo "Node.js and npm upgrade completed. Versions:"
node -v
npm -v

# ============================================
# Git 설치
# ============================================
# Git은 소스 코드에서 빌드하여 설치합니다.
# 이유: 패키지 관리자를 사용할 수 없는 환경이거나 최신 버전이 필요할 때
# 아래 명령어는 Git 소스 코드를 다운로드하고 빌드 및 설치하는 과정입니다.
echo "Installing Git..."
wget https://mirrors.edge.kernel.org/pub/software/scm/git/git-2.42.0.tar.gz
tar -xzf git-2.42.0.tar.gz
cd git-2.42.0
make configure
./configure --prefix=/usr/local
make
sudo make install
cd ..
rm -rf git-2.42.0 git-2.42.0.tar.gz
echo "Git installation completed. Version:"
git --version

# ============================================
# .bashrc 및 .bash_profile 설정
# ============================================
# .bashrc는 비로그인 셸에서 실행되며, 환경 변수를 설정하는 데 사용됩니다.
# .bash_profile은 로그인 셸에서 실행되며, .bashrc를 호출하도록 설정합니다.
# 아래 코드는 .bash_profile을 생성하여 .bashrc를 호출하도록 설정합니다.

# 실행 권한부여. 권한을 수정
chmod +x ~/.bash_profile

echo "Configuring .bash_profile..."
if [ ! -f ~/.bash_profile ]; then
    echo 'if [ -f ~/.bashrc ]; then' > ~/.bash_profile
    echo '    source ~/.bashrc' >> ~/.bash_profile
    echo 'fi' >> ~/.bash_profile
    echo ".bash_profile created and configured."
else
    echo ".bash_profile already exists. Skipping creation."
fi

# ============================================
# sh 셸에서도 .bashrc 실행 설정
# ============================================
# sh 셸이 실행될 때 .bashrc를 자동으로 불러오도록 설정합니다.
echo "Configuring sh shell to load .bashrc..."
if ! grep -q 'export ENV="$HOME/.bashrc"' ~/.profile; then
    echo 'export ENV="$HOME/.bashrc"' >> ~/.profile
    echo ".profile updated to load .bashrc in sh shell."
else
    echo ".profile already configured to load .bashrc."
fi

# .bashrc와 .bash_profile 적용
source ~/.bashrc
source ~/.bash_profile
source ~/.profile

# ============================================
# 최종 확인
# ============================================
# Node.js, npm, Git이 정상적으로 설치되었는지 확인합니다.
echo "Final check:"
node -v
npm -v
git --version

echo "Setup completed successfully!"

# 이 rubikSetting.sh 쉘스크립트 사용방법 
# 이 스크립트를 실행하면 Node.js와 Git이 설치되고, 환경 변수가 설정되며, 모든 설정이 자동으로 적용됩니다.
# 1. chmod +x rubikSetting.sh
# 2. ./rubikSetting.sh