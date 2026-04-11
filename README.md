# irocoro（イロコロ）

気分に応じて、心を安定させる色を提案するWebアプリです。

URL  
https://irocoro.onrender.com/


以下のアカウントでログインして動作確認が可能です。  
ユーザー名: demo_user  
パスワード: Demo1234  


※無料プラン（Render）でデプロイしているため、  
  初回アクセス時は起動に30秒〜1分ほどかかる場合があります。

---

## 概要

irocoroは、ユーザーの「気分」を入力することで、  
その感情に応じた色を提案するアプリです。

現代社会ではストレスや不安を抱える人が増えている一方で、  
自分の感情を客観的に把握する機会は多くありません。

本アプリは、

- 気分の可視化  
- 色彩心理を活用したセルフケア  

を通じて、日常的なメンタルケアを支援することを目的としています。

---

## 作成背景

- 感情を「なんとなく」で処理してしまう課題  
- ストレスの蓄積に気づきにくい問題  

これらを解決するために、  
「気分 × 色」というアプローチで  
直感的に使えるアプリを開発しました。

---

## 主な機能

### 気分入力機能
- テキスト / 選択式 / 絵文字で気分を入力  

### 色提案機能
- 気分を安定させる色を提案

### 履歴管理・感情グラフ
- カレンダー形式で過去の気分を確認  
- 感情の変化を可視化  

### ユーザー管理
- ログイン機能  
- 個人ごとの履歴保存  

---

## 工夫した点  
- 色をHSL（色相・彩度・明度）に変換し、  
  入力された感情の強度に応じて彩度・明度を調整することで、  
  同じ感情でも異なる色表現ができるように工夫しました。  
- 習慣化を意識し、操作のシンプルさを重視したUI設計にしました。  
  入力フローを最小限に抑え、  
  ユーザーがストレスなく気分を記録できることを意識し、  
  日常的に継続しやすいアプリを目指しました。

---

## 苦労した点
- 予算の都合上AIを使用できなかったため、  
  色の提案が固定化してしまう課題がありました。  
- その解決として、  
  HSL値による動的な色変化ロジックを実装し、  
  バリエーションを持たせました。

---

## 今後の課題
- ユーザーごとの傾向分析やフィードバック機能の強化
- 個人差を考慮した色提案の高度化
- ログデータの分析・可視化機能の拡充

---

## 技術スタック

- Backend: Django（認証機能・ORM） / Python  
- Frontend: HTML / CSS / JavaScript  
- DB: PostgreSQL
- デプロイ: Render  

---

## 画面イメージ

### 入力画面
<p align="center">
  <img alt="irocoro_入力" src="https://github.com/user-attachments/assets/fa0c5b1d-6fb9-401c-a5f1-58b2b90ed94f" width="60%">
</p>

### 色提案画面
<p align="center">
  <img alt="irocoro_色提案(上)" src="https://github.com/user-attachments/assets/5555b38c-bc1a-4f15-8020-9469f3090068" width="45%">
  <img alt="irocoro_色提案(下)" src="https://github.com/user-attachments/assets/1c8c7666-ce3d-4c31-97a8-d3d2b2c2e3ec" width="45%">
</p>

### 履歴・可視化機能
<p align="center">
  <img alt="irocoro_カレンダー" src="https://github.com/user-attachments/assets/cb397188-00e2-4729-aa1b-764ddf65149f" width="45%">
  <img alt="irocoro_グラフ" src="https://github.com/user-attachments/assets/d57eba11-7dd1-409e-83fc-79b9645e6cea" width="45%">
</p>  

---
