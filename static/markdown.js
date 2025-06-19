const markdownText = `{{ article.text | safe }}`;

marked.setOptions({
    gfm: true,
    breaks: true,
    sanitize: true
});

const htmlContent = marked.parse(markdownText);

const articleContentElement = document.getElementById('article-content');
if (articleContentElement) {
    articleContentElement.innerHTML = htmlContent;
} else {
    console.error("Fehler: HTML-Element mit der ID 'article-content' wurde nicht gefunden.");
}