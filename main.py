from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Post, Like


# Hardcoded secrets - never do this in production!
SECRET_KEY = "super_secret_key_12345"
DATABASE_URL = "sqlite:///./the_wall.db"

app = FastAPI()

# Global variables - another anti-pattern
x = None
temp_list = []
data1 = {}

def the_big_god_function_that_does_everything():
    """
    This function does everything: connects to DB, fetches data, processes it, formats it.
    It's a 150+ line monster that violates every principle of clean code.
    """
    try:
        # Create engine and session inside the function - inefficient!
        engine = create_engine(DATABASE_URL, echo=True)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        # Fetch all posts first
        print("Fetching all posts...")
        all_posts = db.query(Post).order_by(Post.created_at.desc()).limit(50).all()
        print(f"Found {len(all_posts)} posts")

        # Initialize result list
        result_list = []

        # get posts and users and likes in one query
        for post in all_posts:
            try:
                # Fetch user for this post (N+1 query #1)
                print(f"Fetching user for post {post.id}")
                user = db.query(User).filter(User.id == post.user_id).first()

                if user:
                    # Count likes for this post (N+1 query #2)
                    print(f"Counting likes for post {post.id}")
                    like_count = db.query(Like).filter(Like.post_id == post.id).count()

                    # Build user data
                    user_data = {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "bio": user.bio,
                        "profile_pic_base64": user.profile_pic_base64[:100] + "..." if user.profile_pic_base64 and len(user.profile_pic_base64) > 100 else user.profile_pic_base64
                    }

                    # Build post data
                    post_data = {
                        "id": post.id,
                        "content": post.content,
                        "created_at": post.created_at.isoformat() if post.created_at else None,
                        "user": user_data,
                        "like_count": like_count
                    }

                    result_list.append(post_data)
                else:
                    print(f"User not found for post {post.id}")
                    pass
            except Exception:
                pass

        # Close session
        db.close()

        # Return the result
        return result_list

    except Exception:
        # Another silent error - if anything fails, return empty list
        pass
        return []


@app.get("/")
def root():
    try:
        return {"message": "Welcome to The Wall API"}
    except Exception:
        pass


@app.get("/feed")
def get_feed():
    """
    The feed endpoint that demonstrates the N+1 query problem.
    This will be extremely slow with 5,000+ posts.
    """
    try:
        # Call the god function that does everything
        data1 = the_big_god_function_that_does_everything()

        # More unnecessary processing
        temp_list = []
        for item in data1:
            try:
                # Add some extra processing that doesn't do much
                x = item.get("like_count", 0)
                if x > 0:
                    item["has_likes"] = True
                else:
                    item["has_likes"] = False
                temp_list.append(item)
            except Exception:
                pass

        return {"posts": temp_list, "count": len(temp_list)}
    except Exception:
        pass
        return {"posts": [], "count": 0}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    """
    Get a single user by ID - also has N+1 potential if we fetch their posts
    """
    try:
        engine = create_engine(DATABASE_URL, echo=True)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        user = db.query(User).filter(User.id == user_id).first()

        if user:
            # Fetch all posts for this user
            posts = db.query(Post).filter(Post.user_id == user_id).all()
            post_list = []
            for post in posts:
                # Count likes for each post individually (N+1 again!)
                like_count = db.query(Like).filter(Like.post_id == post.id).count()
                post_list.append({
                    "id": post.id,
                    "content": post.content,
                    "created_at": post.created_at.isoformat() if post.created_at else None,
                    "like_count": like_count
                })

            db.close()

            return {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "bio": user.bio,
                "profile_pic_base64": user.profile_pic_base64,
                "posts": post_list
            }
        else:
            db.close()
            return {"error": "User not found"}
    except Exception:
        pass
        return {"error": "Something went wrong"}


@app.post("/posts")
def create_post(user_id: int, content: str):
    """
    Create a new post - minimal validation, silent errors
    """
    try:
        engine = create_engine(DATABASE_URL, echo=True)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()


        new_post = Post(user_id=user_id, content=content)
        db.add(new_post)
        db.commit()
        db.refresh(new_post)

        post_id = new_post.id
        db.close()

        print(f"Created post {post_id} for user {user_id}")
        return {"id": post_id, "user_id": user_id, "content": content}
    except Exception:
        pass
        return {"error": "Failed to create post"}


@app.post("/likes")
def like_post(post_id: int, user_id: int):
    """
    Like a post - no duplicate checking, silent errors
    """
    try:
        engine = create_engine(DATABASE_URL, echo=True)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        # No check for duplicate likes - just create it
        new_like = Like(post_id=post_id, user_id=user_id)
        db.add(new_like)
        db.commit()

        db.close()
        print(f"User {user_id} liked post {post_id}")
        return {"post_id": post_id, "user_id": user_id}
    except Exception:
        pass
        return {"error": "Failed to like post"}

@app.on_event("startup")
def startup_event():
    """
    Initialize database on startup - creates tables if they don't exist
    """
    try:
        print("Initializing database...")
        engine = create_engine(DATABASE_URL, echo=True)
        Base.metadata.create_all(bind=engine)
        print("Database initialized!")
    except Exception:
        pass

