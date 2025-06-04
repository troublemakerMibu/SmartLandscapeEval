"""词云生成"""
from wordcloud import WordCloud
import jieba
import matplotlib.pyplot as plt
from typing import List, Dict
import os

class WordCloudGenerator:
    def __init__(self):
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 设置停用词
        self.stopwords = set([
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
            '没有', '看', '好', '自己', '这', '他', '她', '那', '但', '与', '并',
            '供应商', '绿化', '服务', '管理', '工作', '项目', '公司', '进行',
            '是否', '如何', '能否', '贵', '您', '或', '及', '可', '无', '请'
        ])

    def create_word_cloud(self, feedbacks: List[Dict], supplier_name: str, save_path: str):
        """创建词云图"""
        # 收集所有文本
        positive_texts = []
        negative_texts = []

        for feedback in feedbacks:
            if feedback:  # 确保feedback不是None
                if 'positive_description' in feedback and feedback['positive_description']:
                    positive_texts.append(str(feedback['positive_description']))
                if 'positive_case' in feedback and feedback['positive_case']:
                    positive_texts.append(str(feedback['positive_case']))
                if 'negative_description' in feedback and feedback['negative_description']:
                    negative_texts.append(str(feedback['negative_description']))
                if 'negative_case' in feedback and feedback['negative_case']:
                    negative_texts.append(str(feedback['negative_case']))
                if 'suggestions' in feedback and feedback['suggestions']:
                    negative_texts.append(str(feedback['suggestions']))

        # 创建图形
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

        # 正面词云
        if positive_texts:
            positive_success = self._generate_single_wordcloud(
                ' '.join(positive_texts),
                ax1,
                '优点词云',
                'Greens'
            )
            if not positive_success:
                ax1.text(0.5, 0.5, '文本过少，无法生成词云', ha='center', va='center',
                        fontsize=16, color='gray')
                ax1.axis('off')
        else:
            ax1.text(0.5, 0.5, '暂无正面反馈', ha='center', va='center', fontsize=20)
            ax1.axis('off')

        # 负面词云
        if negative_texts:
            negative_success = self._generate_single_wordcloud(
                ' '.join(negative_texts),
                ax2,
                '改进建议词云',
                'Reds'
            )
            if not negative_success:
                ax2.text(0.5, 0.5, '文本过少，无法生成词云', ha='center', va='center',
                        fontsize=16, color='gray')
                ax2.axis('off')
        else:
            ax2.text(0.5, 0.5, '暂无改进建议', ha='center', va='center', fontsize=20)
            ax2.axis('off')

        plt.suptitle(f'{supplier_name} - 反馈词云分析', fontsize=20)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _generate_single_wordcloud(self, text: str, ax, title: str, colormap: str) -> bool:
        """生成单个词云，返回是否成功"""
        try:
            # 清理文本
            text = text.strip()
            if not text:
                return False

            # 分词
            words = jieba.lcut(text)
            # 过滤：去除停用词、单字词、纯数字
            words = [w for w in words if len(w) > 1 and w not in self.stopwords and not w.isdigit()]

            if not words:
                return False

            # 统计词频
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1

            # 如果词太少，使用词频图代替词云
            if len(word_freq) < 3:
                return self._create_word_frequency_chart(word_freq, ax, title, colormap)

            # 尝试查找字体文件
            font_path = None
            possible_fonts = [
                'simhei.ttf',
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/simsun.ttc',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/System/Library/Fonts/PingFang.ttc'
            ]

            for font in possible_fonts:
                if os.path.exists(font):
                    font_path = font
                    break

            # 生成词云
            wordcloud = WordCloud(
                font_path=font_path,
                width=800,
                height=600,
                background_color='white',
                colormap=colormap,
                max_words=100,
                relative_scaling=0.5,
                min_font_size=10,
                random_state=42,
                prefer_horizontal=0.7
            ).generate_from_frequencies(word_freq)

            # 显示词云
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.set_title(title, fontsize=16)
            ax.axis('off')
            return True

        except Exception as e:
            print(f"生成词云时出错: {str(e)}")
            return self._create_word_frequency_chart(text, ax, title, colormap)

    def _create_word_frequency_chart(self, data, ax, title: str, color: str) -> bool:
        """创建词频图作为词云的替代"""
        try:
            if isinstance(data, str):
                # 如果是字符串，进行分词
                words = jieba.lcut(data)
                words = [w for w in words if len(w) > 1 and w not in self.stopwords and not w.isdigit()]

                if not words:
                    return False

                # 统计词频
                word_freq = {}
                for word in words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            else:
                word_freq = data

            if not word_freq:
                return False

            # 排序并取前15个
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]

            if not sorted_words:
                return False

            words, counts = zip(*sorted_words)

            # 创建条形图
            y_pos = range(len(words))

            if color == 'Greens':
                bar_color = 'green'
            elif color == 'Reds':
                bar_color = 'red'
            else:
                bar_color = 'blue'

            bars = ax.barh(y_pos, counts, color=bar_color, alpha=0.7)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(words)
            ax.invert_yaxis()
            ax.set_xlabel('出现次数')
            ax.set_title(title, fontsize=16)

            # 添加数值标签
            for i, (bar, count) in enumerate(zip(bars, counts)):
                ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                       str(count), ha='left', va='center', fontsize=10)

            ax.grid(axis='x', alpha=0.3)

            return True

        except Exception as e:
            print(f"创建词频图时出错: {str(e)}")
            return False
