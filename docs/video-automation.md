# 验证是否有iframe

先用console验证好
页面有iframe，但不代表上传按钮再iframe里面
上传不一定有input，有可能是一个div

// 检查所有iframe
console.log("主框架数量:", window.frames.length);
console.log("iframe列表:");
for(let i = 0; i < window.frames.length; i++) {
    try {
        console.log(`frame[${i}]:`, window.frames[i].location.href);
    } catch(e) {
        console.log(`frame[${i}]: 无法访问 (跨域)`);
    }
}
// 检查是否有wujie iframe
document.querySelectorAll('iframe').forEach((el, i) => {
    console.log(`iframe[${i}]:`, el.src || el.srcdoc ? '有src/srcdoc' : '无');
    console.log(`  class:`, el.className);
    console.log(`  id:`, el.id);
});

