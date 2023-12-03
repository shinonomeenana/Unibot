---
sidebar: false
---
# 添加至Discord / Add to Discord

### 中文
[bot使用教程](/usage/)

使用頁面最下方的按鈕添加bot至Discord伺服器

注意：此bot會匹配伺服器內所有訊息，若不希望被誤匹配，建議設置單獨頻道和身分組以確保bot只在專門的頻道回覆訊息。

### English
[Docs](/en/usage/)

Use the following button to add the bot to Discord server

The bot will match all messages within the server. If you don’t want to be disturbed, it’s recommended to set up a separate bot channel and role to ensure the bot is only used in one channel.

<style>
  .custom-button {
    padding: 15px 30px;
    font-size: 16px;
    color: white;
    background-color: #3eaf7c; /* 绿色背景 */
    border: 1px solid transparent;
    border-radius: 4px;
    transition: color 0.3s ease-in-out, background-color 0.3s ease-in-out, border-color 0.3s ease-in-out;
    text-decoration: none !important;
    display: inline-block;
    cursor: pointer;
  }

  .custom-button:hover, .custom-button:focus {
    background-color: #4abf8a; /* 鼠标悬停或聚焦时的深绿色 */
    border-color: #1e7e34;
    color: white;
    text-decoration: none !important;
  }
</style>

<a href="https://discord.com/api/oauth2/authorize?client_id=975690393339457547&permissions=274877908992&scope=bot" class="custom-button">Add to Discord</a>