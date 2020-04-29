# しょぼんのアクション Python版
![shobon](https://user-images.githubusercontent.com/53967490/80561613-01159680-8a20-11ea-9da6-ab9bf67cada4.jpg)

昔流行った某鬼畜ゲーム「しょぼんのアクション」をPythonで１から作り直したものです。  
現時点ではまだ1-1に登場する敵・トラップしか実装していません。

<br>

- 良くなった点
    - 60fps対応。
    - Excelからステージデータが読み取れるため、簡単にステージ改造・自作が出来ます。  
    - Pythonが扱える場合、コードを追加することで簡単に様々な敵やトラップが追加できます。

![excel](https://user-images.githubusercontent.com/53967490/80561615-0246c380-8a20-11ea-9f78-7912d588f526.jpg)

<br>

# ステージの改造方法
resフォルダの中にあるステージデータ.xlsxのシート「1-1」を編集することでステージの改造・自作が出来ます。  
またステージに要素を追加する場合、それぞれステージデータに割り振られている番号を各セルに記入することで追加出来ます。  
（割り振り番号一覧はシート「ステージデータ」にまとめました）  

<br>

尚先程記載した通り、現時点では1-1に登場する敵・トラップのみしか追加していないため作成自由度は低めです。  

![zisaku](https://user-images.githubusercontent.com/53967490/80562923-3a500580-8a24-11ea-999e-05a8d23d61b4.gif)

<br>

- 飛ぶ魚（No.29）について  
   - 設置した場所が土管の真上だった場合、土管の中を初期座標として設定します。  
   （変更箇所: スピード・出現条件を土管の上に立った時に変更）

<br>

- イベントポイント（No.39）について  
   - イベントポイントを設置した場合、その座標を通過した際に画面内に居る「まるい敵（イベント）」が落ちてきます。  
   - どちらか一方が設置されていない場合は何も起こりません。  

<br>

# ゲーム自体の改造を行いたい場合
### 実行に必要なものをインストール
- Python 3.8.2  
<br>

コマンドプロンプトにて下記のコマンドを実行し、作業フォルダを変更します。  
※ ダウンロードした場所によって各自変更して下さい
```
(例)
cd C:\Users\(ユーザー名)\Downloads\ShobonAction-master\ShobonAction-master
```
<br>

次に下記のコマンドを実行し、必要なモジュールをインストールします。  
```
pip install -r requirements.txt
```
<br>

これでインストールは完了です。  
Visual Studioなりメモ帳なりお好きな開発環境で編集してください。

![notepad](https://user-images.githubusercontent.com/53967490/80544582-520b9780-89ec-11ea-9746-e39f21f705c0.png)

<br><br>

### 完成したゲームのexe化
Pythonをインストールしてない人でもゲームをプレイできるよう、cx_Freezeモジュールを使用してexeファイルに変換することが出来ます。  

<br>

先程と同様に下記のコマンドを実行し、作業フォルダを変更します。  
```
(例)
cd C:\Users\(ユーザー名)\Downloads\ShobonAction-master\ShobonAction-master
```
<br>

次に下記のコマンドを実行するとexeファイルへの変換を開始します。
```
python convert_into_exe.py build
```
<br>

変換が完了するとこのようなディレクトリ構成が出来上がります。  
その後、exe.win-amd64-3.8ディレクトリに手動でres、BGM、SEフォルダをコピーするとexeファイルが起動できるようになります。
```
└─build
   └─exe.win-amd64-3.8
       │  api-ms-win-crt-heap-l1-1-0.dll
       │  api-ms-win-crt-locale-l1-1-0.dll
       │  api-ms-win-crt-math-l1-1-0.dll
       │  api-ms-win-crt-runtime-l1-1-0.dll
       │  api-ms-win-crt-stdio-l1-1-0.dll
       │  python38.dll
       │  ShobonAction.exe
       └─lib  
```
⇓

```
└─build
   └─exe.win-amd64-3.8
       │  api-ms-win-crt-heap-l1-1-0.dll
       │  api-ms-win-crt-locale-l1-1-0.dll
       │  api-ms-win-crt-math-l1-1-0.dll
       │  api-ms-win-crt-runtime-l1-1-0.dll
       │  api-ms-win-crt-stdio-l1-1-0.dll
       │  python38.dll
       │  ShobonAction.exe
       ├─lib   
       ├─BGM  
       ├─res    
       └─SE
```
<br>


また１クリックで一連の動作を行えるよう、batスクリプトを組んでおきましたので良ければ使って下さい。   
（ただし環境によっては上手く動かない場合があります）
```
cd /d %~dp0
convert_into_exe.py build
xcopy .\res .\build\exe.win-amd64-3.8\res /s/e/i/y
xcopy .\SE .\build\exe.win-amd64-3.8\SE /s/e/i/y
xcopy .\BGM .\build\exe.win-amd64-3.8\BGM /s/e/i/y
pause
```
![bat file](https://user-images.githubusercontent.com/53967490/80553262-20062f80-8a04-11ea-84a3-2abd6c2e36ad.gif)
<br>

# 制作者

| **Python版制作者**  | **3939**    |
|:------------------:|:-----------:|
| **原作者**          | **ちく**    |
| **画像・BGM・SE**   | **ちく**    |
<br>

>ちくさん制作のしょぼんのアクションへのリンク   
> <http://chibicon.net/slink/j062101/>
<br>
