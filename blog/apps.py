from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = 'blog'
    # 分页
    paginate = 10
    # 页面设置
    title = 'pktangyue'
    excerpt_separator = '<!-- more -->'

    def to_dict(self):
        names = (
            'title',
            'excerpt_separator',
        )

        d = {}
        for name in names:
            value = getattr(self, name, None)
            if value:
                d[name] = value

        return d
