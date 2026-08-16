from agents.research_agent import researchApp
from agents.writer_agent import writerApp
from rich import print



# topic = input("enter a topic you want to research:")
# print("-------starting Reseach Pipeline--------")
# research_data = researchApp.invoke({"topic":topic})

# print(research_data)

print("-------starting Writer Pipeline--------")
inputState = {
    "topic": "AI in computerscience",
    "papers": [
        {
            'title': 'AI technologies for education: Recent research &amp; future directions',
            'year': 2021,
            'citations': 854,
            'doi': 'https://doi.org/10.1016/j.caeai.2021.100025',
            'url': 'https://www.sciencedirect.com/science/article/pii/S2666920X21000199/pdf',
            'abstract': """From unique educational perspectives, this article reports a comprehensive review of selected
                        empirical studies on artificial intelligence in education (AIEd) published in 1993–2020, as collected in the Web of Sciences
                        database and selected AIEd-specialized journals. A total of 40 empirical studies met all selection criteria, and were fully
                        reviewed using multiple methods, including selected bibliometrics, content analysis and categorical meta-trends analysis.
                        This article reports the current state of AIEd research, highlights selected AIEd technologies and applications, reviews
                        their proven and potential benefits for education, bridges the gaps between AI technological innovations and their
                        educational applications, and generates practical examples and inspirations for both technological experts that create AIEd
                        technologies and educators who spearhead AI innovations in education. It also provides rich discussions on practical
                        implications and future research directions from multiple perspectives. The advancement of AIEd calls for critical
                        initiatives to address AI ethics and privacy concerns, and requires interdisciplinary and transdisciplinary collaborations
                        in large-scaled, longitudinal research and development efforts.""",
            'local_path': None,
            'authors': ['Ke Zhang', 'Ayse Begum Aslan'],
            'publisher_url': 'https://doi.org/10.1016/j.caeai.2021.100025'
        },
        {
            'title': 'Towards Human-Centered Explainable AI: A Survey of User Studies for Model Explanations',
            'year': 2023,
            'citations': 234,
            'doi': 'https://doi.org/10.1109/tpami.2023.3331846',
            'url': 'https://ieeexplore.ieee.org/ielx7/34/4359286/10316181.pdf',
            'abstract': """Explainable AI (XAI) is widely viewed as a sine qua non for ever-expanding AI research. A better
                        understanding of the needs of XAI users, as well as human-centered evaluations of explainable models are both a necessity
                        and a challenge. In this paper, we explore how human-computer interaction (HCI) and AI researchers conduct user studies in
                        XAI applications based on a systematic literature review. After identifying and thoroughly analyzing 97 core papers with
                        human-based XAI evaluations over the past five years, we categorize them along the measured characteristics of explanatory
                        methods, namely trust, understanding, usability, and human-AI collaboration performance. Our research shows that XAI is
                        spreading more rapidly in certain application domains, such as recommender systems than in others, but that user evaluations
                        are still rather sparse and incorporate hardly any insights from cognitive or social sciences. Based on a comprehensive
                        discussion of best practices, i.e., common models, design choices, and measures in user studies, we propose practical
                        guidelines on designing and conducting user studies for XAI researchers and practitioners. Lastly, this survey also
                        highlights several open research directions, particularly linking psychological science and human-centered XAI.""",
            'local_path': None,
            'authors': [
                'Yao Rong',
                'Tobias Leemann',
                'Thai-Trang Nguyen',
                'Lisa Fiedler',
                'Peizhu Qian',
                'Vaibhav Unhelkar',
                'Tina Seidel',
                'Gjergji Kasneci',
                'Enkelejda Kasneci'
            ],
            'publisher_url': 'https://doi.org/10.1109/tpami.2023.3331846'
        },
         {
            'title': 'Artificial intelligence (AI) learning tools in K-12 education: A\xa0scoping review',
            'year': 2024,
            'citations': 212,
            'doi': 'https://doi.org/10.1007/s40692-023-00304-9',
            'url': 'https://link.springer.com/content/pdf/10.1007/s40692-023-00304-9.pdf',
            'abstract': """Abstract Artificial intelligence (AI) literacy is a global strategic objective in education.
                        However, little is known about how AI should be taught. In this paper, 46 studies in academic conferences and journals are
                        reviewed to investigate pedagogical strategies, learning tools, assessment methods in AI literacy education in K-12
                        contexts, and students’ learning outcomes. The investigation reveals that the promotion of AI literacy education has seen
                        significant progress in the past two decades. This highlights that intelligent agents, including Google’s Teachable Machine,
                        Learning ML, and Machine Learning for Kids, are age-appropriate tools for AI literacy education in K-12 contexts.
                        Kindergarten students can benefit from learning tools such as PopBots, while software devices, such as Scratch and Python,
                        which help to develop the computational thinking of AI algorithms, can be introduced to both primary and secondary schools.
                        The research shows that project-based, human–computer collaborative learning and play- and game-based approaches, with
                        constructivist methodologies, have been applied frequently in AI literacy education. Cognitive, affective, and behavioral
                        learning outcomes, course satisfaction and soft skills acquisition have been reported. The paper informs educators of
                        appropriate learning tools, pedagogical strategies, assessment methodologies in AI literacy education, and students’
                        learning outcomes. Research implications and future research directions within the K-12 context are also discussed.""",
            'local_path': 'paper\\10_1007_s40692-023-00304-9.pdf',
            'authors': ['Iris Heung Yue Yim', 'Jiahong Su'],
            'publisher_url': 'https://doi.org/10.1007/s40692-023-00304-9'
        },
         {
            'title': 'Artificial Intelligence and Business Value: a Literature Review',
            'year': 2021,
            'citations': 947,
            'doi': 'https://doi.org/10.1007/s10796-021-10186-w',
            'url': 'https://link.springer.com/content/pdf/10.1007/s10796-021-10186-w.pdf',
            'abstract': """Abstract Artificial Intelligence (AI) are a wide-ranging set of technologies that promise several
                        advantages for organizations in terms off added business value. Over the past few years, organizations are increasingly
                        turning to AI in order to gain business value following a deluge of data and a strong increase in computational capacity.
                        Nevertheless, organizations are still struggling to adopt and leverage AI in their operations. The lack of a coherent
                        understanding of how AI technologies create business value, and what type of business value is expected, therefore
                        necessitates a holistic understanding. This study provides a systematic literature review that attempts to explain how
                        organizations can leverage AI technologies in their operations and elucidate the value-generating mechanisms. Our analysis
                        synthesizes the current literature and highlights: (1) the key enablers and inhibitors of AI adoption and use; (2) the
                        typologies of AI use in the organizational setting; and (3) the first- and second-order effects of AI. The paper concludes
                        with an identification of the gaps in the literature and develops a research agenda that identifies areas that need to be
                        addressed by future studies.""",
            'local_path': 'paper\\10_1007_s10796-021-10186-w.pdf',
            'authors': ['Ida Merete Enholm', 'Emmanouil Papagiannidis', 'Patrick Mikalef', 'John Krogstie'],
            'publisher_url': 'https://doi.org/10.1007/s10796-021-10186-w'
        },
        #  {
        #     'title': 'AI for the Common Good?! Pitfalls, challenges, and ethics pen-testing',
        #     'year': 2019,
        #     'citations': 102,
        #     'doi': 'https://doi.org/10.1515/pjbr-2019-0004',
        #     'url': 'https://www.degruyter.com/downloadpdf/journals/pjbr/10/1/article-p44.pdf',
        #     'abstract': """Recently, many AI researchers and practitioners have embarked on research visions that involve
        #                 doing AI for “Good”. This is part of a general drive towards infusing AI research and practice with ethical thinking. One
        #                 frequent theme in current ethical guidelines is the requirement that AI be good for all, or: contribute to the Common Good.
        #                 Butwhat is the Common Good, and is it enough to want to be good? Via four lead questions, I will illustrate challenges and
        #                 pitfallswhen determining, from an AI point of view,what the Common Good is and how it can be enhanced by AI. The questions
        #                 are: What is the problem / What is a problem?, Who defines the problem?, What is the role of knowledge?, and What are
        #                 important side effects and dynamics? The illustration will use an example from the domain of “AI for Social Good”, more
        #                 specifically “Data Science for Social Good”. Even if the importance of these questions may be known at an abstract level,
        #                 they do not get asked sufficiently in practice, as shown by an exploratory study of 99 contributions to recent conferences
        #                 in the field. Turning these challenges and pitfalls into a positive recommendation, as a conclusion I will draw on another
        #                 characteristic of computer-science thinking and practice to make these impediments visible and attenuate them: “attacks” as
        #                 a method for improving design. This results in the proposal of ethics pen-testing as a method for helping AI designs to
        #                 better contribute to the Common Good.""",
        #     'local_path': 'paper\\10_1515_pjbr-2019-0004.pdf',
        #     'authors': ['Bettina Berendt'],
        #     'publisher_url': 'https://doi.org/10.1515/pjbr-2019-0004'
        # }
    ]
}

writer_data = writerApp.invoke(inputState)

print(writer_data['starter_manuscript'])