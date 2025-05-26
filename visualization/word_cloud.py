"""词云生成"""
from wordcloud import WordCloud
import jieba
import matplotlib.pyplot as plt
from typing import List, Dict

class WordCloudGenerator:
    def __init__(self):
        # 设置停用词
        self.stopwords = set([
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
            '没有', '看', '好', '自己', '这', '他', '她', '那', '但', '与', '并',
            '供应商', '绿化', '服务', '管理', '工作', '项目', '公司', '进行'
        ])

    def create_word_cloud(self, feedbacks: List[Dict], supplier_name: str, save_path: str):
        """创建词云图"""
        # 收集所有文本
        positive_texts = []
        negative_texts = []

        for feedback in feedbacks:
            if 'positive_description' in feedback:
                positive_texts.append(feedback['positive_description'])
            if 'negative_description' in feedback:
                negative_texts.append(feedback['negative_description'])
            if 'suggestions' in feedback:
                negative_texts.append(feedback['suggestions'])

        # 创建图形
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

        # 正面词云
        if positive_texts:
            self._generate_single_wordcloud(
                ' '.join(positive_texts),
                ax1,
                '优点词云',
                'Greens'
            )
        else:
            ax1.text(0.5, 0.5, '暂无正面反馈', ha='center', va='center', fontsize=20)
            ax1.axis('off')

        # 负面词云
        if negative_texts:
            self._generate_single_wordcloud(
                ' '.join(negative_texts),
                ax2,
                '改进建议词云',
                'Reds'
            )
        else:
            ax2.text(0.5, 0.5, '暂无改进建议', ha='center', va='center', fontsize=20)
            ax2.axis('off')

        plt.suptitle(f'{supplier_name} - 反馈词云分析', fontsize=20)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _generate_single_wordcloud(self, text: str, ax, title: str, colormap: str):
        """生成单个词云"""
        # 分词
        words = jieba.lcut(text)
        words = [w for w in words if len(w) > 1 and w not in self.stopwords]

        # 生成词云
        wordcloud = WordCloud(
            font_path='simhei.ttf',  # 需要提供中文字体文件
            width=800,
            height=600,
            background_color='white',
            colormap=colormap,
            max_words=100,
            relative_scaling=0.5,
            min_font_size=10
        ).generate(' '.join(words))

        # 显示词云
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.set_title(title, fontsize=16)
        ax.axis('off')
