from langgraph.graph import StateGraph, END

from state import PosterState
from nodes.fetch_news import fetch_all_news
from nodes.rank_articles import rank_articles
from nodes.write_post import write_post
from nodes.review_agent import review_agent, route_review
from nodes.notify_telegram import notify_telegram
from nodes.post_linkedin import post_linkedin


def build_graph() -> StateGraph:
    graph = StateGraph(PosterState)

    graph.add_node("fetch_news", fetch_all_news)
    graph.add_node("rank_articles", rank_articles)
    graph.add_node("write_post", write_post)
    graph.add_node("review_agent", review_agent)
    graph.add_node("notify_telegram", notify_telegram)
    graph.add_node("post_linkedin", post_linkedin)

    graph.set_entry_point("fetch_news")
    graph.add_edge("fetch_news", "rank_articles")
    graph.add_edge("rank_articles", "write_post")
    graph.add_edge("write_post", "review_agent")

    graph.add_conditional_edges(
        "review_agent",
        route_review,
        {
            "write_post": "write_post",
            "notify_telegram": "notify_telegram",
            "end": END,
        },
    )

    graph.add_edge("notify_telegram", "post_linkedin")
    graph.add_edge("post_linkedin", END)

    return graph.compile()
