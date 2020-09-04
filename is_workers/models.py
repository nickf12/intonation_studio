from dataclasses import dataclass


@dataclass
class YoutubeVideo:
    file: str
    title: str
    description: str = 'Intonation analysis of the sentence.'
    category: str = ''
    keywords: str = 'pronunciation, intonation'
    privacyStatus: str = 'public'
