from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Post, Like
from datetime import datetime, timedelta, timezone
import random
import string
import base64
from faker import Faker

# Initialize Faker
fake = Faker()

# Hardcoded database URL - same anti-pattern as main.py
DATABASE_URL = "sqlite:///./the_wall.db"

def generate_random_string(length=50):
    """Generate a random string"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_base64_image():
    """Generate a fake base64 encoded image (just random data)"""
    # Generate a large base64 string to simulate an image
    fake_image_data = ''.join(random.choices(string.ascii_letters + string.digits, k=50000))
    return base64.b64encode(fake_image_data.encode()).decode()

def seed_database():
    """Seed the database with 100 users and 5,000 posts"""
    print("Starting database seed...")

    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Clear existing data
    print("Clearing existing data...")
    db.query(Like).delete()
    db.query(Post).delete()
    db.query(User).delete()
    db.commit()

    # Create 100 users
    print("Creating 100 users...")
    users = []
    for i in range(1, 101):
        user = User(
            name=fake.name(),
            email=fake.email(),
            bio=fake.text(max_nb_chars=200),
            profile_pic_base64=generate_base64_image()
        )
        users.append(user)
        db.add(user)

    db.commit()
    print("Users created!")

    # Refresh users to get their IDs
    db.refresh(users[0])
    user_ids = [user.id for user in users]

    # Create 5,000 posts
    print("Creating 5,000 posts...")
    posts = []
    base_date = datetime.now(timezone.utc)

    for i in range(1, 5001):
        # Random user
        user_id = random.choice(user_ids)

        # Random content
        content = f"This is post #{i}. " + generate_random_string(100)

        # Random date within last 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        created_at = base_date - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

        post = Post(
            user_id=user_id,
            content=content,
            created_at=created_at
        )
        posts.append(post)
        db.add(post)

        # Commit in batches to avoid memory issues
        if i % 500 == 0:
            db.commit()
            print(f"Created {i} posts...")

    db.commit()
    print("Posts created!")

    # Refresh posts to get their IDs
    db.refresh(posts[0])
    post_ids = [post.id for post in posts]

    # Create some likes (random distribution)
    print("Creating likes...")
    like_count = 0
    for post_id in post_ids:

        if random.random() < 0.3:
            # Each liked post gets 1-10 random likes
            num_likes = random.randint(1, 10)
            likers = random.sample(user_ids, min(num_likes, len(user_ids)))

            for liker_id in likers:
                like = Like(post_id=post_id, user_id=liker_id)
                db.add(like)
                like_count += 1

    db.commit()
    print(f"Created {like_count} likes!")

    db.close()
    print("Database seeding complete!")
    print(f"Summary:")
    print(f"  - Users: 100")
    print(f"  - Posts: 5,000")
    print(f"  - Likes: {like_count}")

if __name__ == "__main__":
    seed_database()

