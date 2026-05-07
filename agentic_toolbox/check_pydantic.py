"""
Restaurant recommendation system demonstrating context features with multiple customers.
Shows how context helps personalize and improve recommendations over time.
"""

from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime
from pydantic_ai import Agent, RunContext

import json

import logfire

logfire.configure()  
logfire.info('Starting in pydantic_restaurant_context.py')

from pathlib import Path
import json
from datetime import datetime
import os

# Constants for persistence
CONTEXT_DIR = Path("customer_contexts")
CONTEXT_DIR.mkdir(exist_ok=True)

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class ContextPersistence:
    """Handles saving and loading of customer contexts."""
    
    @staticmethod
    def get_context_file(customer_name: str) -> Path:
        """Get the path to a customer's context file."""
        return CONTEXT_DIR / f"{customer_name.lower()}_context.json"
    
    @staticmethod
    def save_context(customer_ctx: 'CustomerContext') -> None:
        """Save customer context to file."""
        context_file = ContextPersistence.get_context_file(customer_ctx.name)
        
        # Convert context to serializable format
        context_data = {
            'name': customer_ctx.name,
            'preferences': customer_ctx.preferences.model_dump(),
            'visit_history': [visit.model_dump() for visit in customer_ctx.visit_history],
            'recommendation_history': [rest.model_dump() for rest in customer_ctx.recommendation_history],
            'context_updates': customer_ctx.context_updates,
            'last_updated': datetime.now().isoformat()
        }
        
        # Save to file with custom encoder
        with open(context_file, 'w') as f:
            json.dump(context_data, f, indent=2, cls=DateTimeEncoder)
        print(f"\n💾 Saved context for {customer_ctx.name} to {context_file}")
    
    @staticmethod
    def load_context(customer_name: str) -> Optional['CustomerContext']:
        """Load customer context from file if it exists."""
        context_file = ContextPersistence.get_context_file(customer_name)
        
        if not context_file.exists():
            print(f"\n📝 No saved context found for {customer_name}")
            return None
        
        try:
            with open(context_file, 'r') as f:
                data = json.load(f)
            
            # Convert ISO format strings back to datetime
            if 'visit_history' in data:
                for visit in data['visit_history']:
                    if 'date' in visit:
                        visit['date'] = datetime.fromisoformat(visit['date'])
            
            # Create new context with loaded data
            preferences = CustomerPreferences(**data['preferences'])
            context = CustomerContext(data['name'], preferences)
            
            # Restore visit history
            context.visit_history = [
                DiningExperience(**visit) for visit in data['visit_history']
            ]
            
            # Restore recommendation history
            context.recommendation_history = [
                Restaurant(**rest) for rest in data['recommendation_history']
            ]
            
            # Restore context updates
            context.context_updates = data['context_updates']
            
            print(f"\n📂 Loaded saved context for {customer_name}")
            print(f"Last updated: {data['last_updated']}")
            return context
            
        except Exception as e:
            print(f"\n❌ Error loading context for {customer_name}: {str(e)}")
            return None

# Models for restaurant recommendations
class Restaurant(BaseModel):
    """Restaurant details."""
    name: str
    cuisine: str
    price_range: Literal["$", "$$", "$$$", "$$$$"]
    vegetarian_friendly: bool = False
    gluten_free_options: bool = False
    average_rating: float
    specialties: List[str]
    location: str
    typical_wait_time: str

class DiningExperience(BaseModel):
    """Record of a customer's dining experience."""
    restaurant: str
    date: datetime
    rating: int
    liked_dishes: List[str]
    disliked_dishes: List[str]
    comments: str
    party_size: int
    occasion: Optional[str] = None

class CustomerPreferences(BaseModel):
    """Customer's dining preferences."""
    favorite_cuisines: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)
    preferred_price_range: List[str] = Field(default_factory=list)
    typical_party_size: int = 2
    favorite_restaurants: List[str] = Field(default_factory=list)
    disliked_restaurants: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    usual_occasions: List[str] = Field(default_factory=list)

class RecommendationContext(BaseModel):
    """Context for restaurant recommendations."""
    customer_name: str
    preferences: CustomerPreferences
    dining_history: List[DiningExperience] = Field(default_factory=list)
    current_request: str
    previous_recommendations: List[Restaurant] = Field(default_factory=list)
    rejected_recommendations: List[Restaurant] = Field(default_factory=list)
    current_occasion: Optional[str] = None
    party_size: Optional[int] = None
    time_of_day: Optional[str] = None

class CustomerContext:
    """Tracks a customer's context across multiple restaurant visits."""
    def __init__(self, name: str, initial_preferences: CustomerPreferences):
        self.name = name
        self.preferences = initial_preferences
        self.visit_history: List[DiningExperience] = []
        self.recommendation_history: List[Restaurant] = []
        self.context_updates: List[dict] = []  # Track all context changes
    
    def add_visit(self, experience: DiningExperience, restaurant: Restaurant):
        """Add a new restaurant visit and update context."""
        self.visit_history.append(experience)
        self.recommendation_history.append(restaurant)
        
        # Store context state before update
        before_state = self.preferences.model_dump()
        
        # Update preferences based on experience
        if experience.rating >= 4:
            if restaurant.name not in self.preferences.favorite_restaurants:
                self.preferences.favorite_restaurants.append(restaurant.name)
            if restaurant.cuisine not in self.preferences.favorite_cuisines:
                self.preferences.favorite_cuisines.append(restaurant.cuisine)
        elif experience.rating <= 2:
            if restaurant.name not in self.preferences.disliked_restaurants:
                self.preferences.disliked_restaurants.append(restaurant.name)
        
        # Update party size preference
        self.preferences.typical_party_size = (
            (self.preferences.typical_party_size * 2 + experience.party_size) // 3
        )
        
        # Update occasion preferences
        if experience.occasion and experience.occasion not in self.preferences.usual_occasions:
            self.preferences.usual_occasions.append(experience.occasion)
        
        # Store context update
        after_state = self.preferences.model_dump()
        self.context_updates.append({
            'visit_number': len(self.visit_history),
            'restaurant': restaurant.name,
            'before': before_state,
            'after': after_state,
            'changes': self._get_context_changes(before_state, after_state),
            'timestamp': datetime.now().isoformat()
        })
        
        # Save context after update
        ContextPersistence.save_context(self)
    
    def _get_context_changes(self, before: dict, after: dict) -> dict:
        """Get changes between two context states."""
        changes = {}
        for key in set(before.keys()) | set(after.keys()):
            if key not in before:
                changes[key] = {'type': 'added', 'value': after[key]}
            elif key not in after:
                changes[key] = {'type': 'removed', 'value': before[key]}
            elif before[key] != after[key]:
                if isinstance(before[key], list):
                    added = set(after[key]) - set(before[key])
                    removed = set(before[key]) - set(after[key])
                    if added or removed:
                        changes[key] = {
                            'type': 'list_changed',
                            'added': list(added),
                            'removed': list(removed)
                        }
                else:
                    changes[key] = {
                        'type': 'value_changed',
                        'from': before[key],
                        'to': after[key]
                    }
        return changes
    
    def print_context_journey(self):
        """Print the customer's context evolution through their restaurant journey."""
        print(f"\n🗺️ Context Journey for {self.name}")
        print("=" * 50)
        
        for i, update in enumerate(self.context_updates, 1):
            print(f"\n📍 Visit #{i}: {update['restaurant']}")
            changes = update['changes']
            
            for key, change in changes.items():
                if change['type'] == 'added':
                    print(f"+ Added {key}: {change['value']}")
                elif change['type'] == 'removed':
                    print(f"- Removed {key}: {change['value']}")
                elif change['type'] == 'list_changed':
                    if change['added']:
                        print(f"+ Added to {key}: {change['added']}")
                    if change['removed']:
                        print(f"- Removed from {key}: {change['removed']}")
                elif change['type'] == 'value_changed':
                    print(f"~ Changed {key}: {change['from']} → {change['to']}")
            
            print(f"\nCurrent preferences after visit:")
            visit_prefs = update['after']
            print(f"- Favorite cuisines: {visit_prefs['favorite_cuisines']}")
            print(f"- Favorite restaurants: {visit_prefs['favorite_restaurants']}")
            if visit_prefs['disliked_restaurants']:
                print(f"- Disliked restaurants: {visit_prefs['disliked_restaurants']}")
            print(f"- Typical party size: {visit_prefs['typical_party_size']}")
            print("-" * 50)

# Initialize recommendation agent
recommendation_agent = Agent(
    model="ollama:qwen2.5:32b",
    result_type=Restaurant,
    deps_type=RecommendationContext,
    system_prompt="""You are a knowledgeable restaurant recommendation agent.
    Analyze customer preferences, dining history, and current context to suggest restaurants they'll love.
    Consider dietary restrictions, price preferences, and past experiences."""
)

@recommendation_agent.system_prompt
async def add_recommendation_context(ctx: RunContext[RecommendationContext]) -> str:
    """Generate a smart recommendation prompt based on customer context."""
    prompt = f"""Recommend a restaurant for {ctx.deps.customer_name}.
    
Current request: {ctx.deps.current_request}
Customer preferences:"""
    
    prefs = ctx.deps.preferences
    if prefs.favorite_cuisines:
        prompt += f"\n- Favorite cuisines: {', '.join(prefs.favorite_cuisines)}"
    if prefs.dietary_restrictions:
        prompt += f"\n- Dietary restrictions: {', '.join(prefs.dietary_restrictions)}"
    if prefs.preferred_price_range:
        prompt += f"\n- Price range: {', '.join(prefs.preferred_price_range)}"
    if prefs.typical_party_size:
        prompt += f"\n- Usually dines with: {prefs.typical_party_size} people"
    if prefs.favorite_restaurants:
        prompt += f"\n- Favorite restaurants: {', '.join(prefs.favorite_restaurants)}"
    if prefs.preferred_locations:
        prompt += f"\n- Preferred locations: {', '.join(prefs.preferred_locations)}"
    
    if ctx.deps.dining_history:
        prompt += "\n\nRecent dining experiences:"
        recent_experiences = sorted(ctx.deps.dining_history, key=lambda x: x.date, reverse=True)[:3]
        for exp in recent_experiences:
            prompt += f"\n- {exp.restaurant} ({exp.date.strftime('%Y-%m-%d')})"
            prompt += f"\n  Rating: {exp.rating}/5"
            prompt += f"\n  Liked: {', '.join(exp.liked_dishes)}"
            if exp.disliked_dishes:
                prompt += f"\n  Disliked: {', '.join(exp.disliked_dishes)}"
    
    if ctx.deps.rejected_recommendations:
        prompt += "\n\nPreviously rejected suggestions:"
        for rest in ctx.deps.rejected_recommendations:
            prompt += f"\n- {rest.name} ({rest.cuisine}, {rest.price_range})"
        prompt += "\nPlease suggest different restaurants from these."
    
    current_context = []
    if ctx.deps.current_occasion:
        current_context.append(f"Occasion: {ctx.deps.current_occasion}")
    if ctx.deps.party_size:
        current_context.append(f"Party size: {ctx.deps.party_size}")
    if ctx.deps.time_of_day:
        current_context.append(f"Time: {ctx.deps.time_of_day}")
    
    if current_context:
        prompt += "\n\nCurrent context:"
        prompt += "\n- " + "\n- ".join(current_context)
    
    return prompt

def print_context_update(title: str, before: dict, after: dict) -> None:
    """Print changes in context in a readable format."""
    print(f"\n📊 {title}")
    print("Changes detected:")
    
    for key in set(before.keys()) | set(after.keys()):
        if key not in before:
            print(f"+ Added {key}: {after[key]}")
        elif key not in after:
            print(f"- Removed {key}: {before[key]}")
        elif before[key] != after[key]:
            if isinstance(before[key], list):
                # Handle list changes
                added = set(after[key]) - set(before[key])
                removed = set(before[key]) - set(after[key])
                if added:
                    print(f"+ Added to {key}: {added}")
                if removed:
                    print(f"- Removed from {key}: {removed}")
            else:
                print(f"~ Changed {key}: {before[key]} → {after[key]}")

# Example restaurant database
RESTAURANTS = {
    "Bella Italia": Restaurant(
        name="Bella Italia",
        cuisine="Italian",
        price_range="$$",
        vegetarian_friendly=True,
        gluten_free_options=True,
        average_rating=4.5,
        specialties=["Margherita Pizza", "Eggplant Parmesan", "Homemade Pasta"],
        location="Downtown",
        typical_wait_time="20-30 minutes"
    ),
    "Sushi Master": Restaurant(
        name="Sushi Master",
        cuisine="Japanese",
        price_range="$$$",
        vegetarian_friendly=True,
        gluten_free_options=True,
        average_rating=4.8,
        specialties=["Omakase", "Dragon Roll", "Fresh Sashimi"],
        location="Marina District",
        typical_wait_time="30-45 minutes"
    ),
    "The Prime Cut": Restaurant(
        name="The Prime Cut",
        cuisine="Steakhouse",
        price_range="$$$$",
        vegetarian_friendly=False,
        gluten_free_options=True,
        average_rating=4.7,
        specialties=["Ribeye Steak", "Wagyu Beef", "Lobster Tail"],
        location="Financial District",
        typical_wait_time="45-60 minutes"
    ),
    "Thai Spice": Restaurant(
        name="Thai Spice",
        cuisine="Thai",
        price_range="$$",
        vegetarian_friendly=True,
        gluten_free_options=True,
        average_rating=4.4,
        specialties=["Pad Thai", "Green Curry", "Mango Sticky Rice"],
        location="Hayes Valley",
        typical_wait_time="15-20 minutes"
    )
}

# Customer database simulation
CUSTOMERS = {
    "Alice": CustomerPreferences(
        favorite_cuisines=["Italian", "Thai"],
        dietary_restrictions=["Vegetarian"],
        preferred_price_range=["$", "$$"],
        typical_party_size=4,
        preferred_locations=["Downtown", "Hayes Valley"],
        usual_occasions=["Family dinner", "Casual dining"]
    ),
    "Bob": CustomerPreferences(
        favorite_cuisines=["Japanese", "Steakhouse"],
        dietary_restrictions=["Gluten-free"],
        preferred_price_range=["$$$", "$$$$"],
        typical_party_size=2,
        preferred_locations=["Financial District", "Marina District"],
        usual_occasions=["Business dinner", "Special occasion"]
    )
}

# Initialize or load customer contexts
CUSTOMER_CONTEXTS = {}
for name, prefs in CUSTOMERS.items():
    # Try to load existing context
    loaded_context = ContextPersistence.load_context(name)
    if loaded_context:
        CUSTOMER_CONTEXTS[name] = loaded_context
    else:
        # Create new context if none exists
        CUSTOMER_CONTEXTS[name] = CustomerContext(name, prefs)

async def update_customer_preferences(
    preferences: CustomerPreferences,
    restaurant: Restaurant,
    experience: DiningExperience
) -> CustomerPreferences:
    """Update customer preferences based on their dining experience."""
    
    # Store original state for comparison
    original_state = preferences.model_dump()
    
    # Update favorite restaurants if highly rated
    if experience.rating >= 4:
        if restaurant.name not in preferences.favorite_restaurants:
            preferences.favorite_restaurants.append(restaurant.name)
        if restaurant.cuisine not in preferences.favorite_cuisines:
            preferences.favorite_cuisines.append(restaurant.cuisine)
    
    # Update disliked restaurants if poorly rated
    elif experience.rating <= 2:
        if restaurant.name not in preferences.disliked_restaurants:
            preferences.disliked_restaurants.append(restaurant.name)
    
    # Update typical party size (weighted average)
    preferences.typical_party_size = (
        (preferences.typical_party_size * 2 + experience.party_size) // 3
    )
    
    # Update occasion preferences
    if experience.occasion and experience.occasion not in preferences.usual_occasions:
        preferences.usual_occasions.append(experience.occasion)
    
    # Show context updates
    print_context_update(
        f"Context Updates for {experience.restaurant}",
        original_state,
        preferences.model_dump()
    )
    
    return preferences

async def get_restaurant_recommendation(
    customer_name: str,
    request: str,
    occasion: Optional[str] = None,
    party_size: Optional[int] = None,
    time_of_day: Optional[str] = None
) -> Optional[Restaurant]:
    """Get a personalized restaurant recommendation for a customer."""
    
    try:
        # Get customer preferences
        preferences = CUSTOMERS.get(customer_name)
        if not preferences:
            raise ValueError(f"Customer {customer_name} not found")
        
        # Show initial context
        print(f"\n📋 Initial Context for {customer_name}:")
        print(f"Favorite cuisines: {preferences.favorite_cuisines}")
        print(f"Dietary restrictions: {preferences.dietary_restrictions}")
        print(f"Price range: {preferences.preferred_price_range}")
        print(f"Typical party size: {preferences.typical_party_size}")
        if preferences.favorite_restaurants:
            print(f"Favorite restaurants: {preferences.favorite_restaurants}")
        if preferences.disliked_restaurants:
            print(f"Disliked restaurants: {preferences.disliked_restaurants}")
        
        # Create recommendation context
        context = RecommendationContext(
            customer_name=customer_name,
            preferences=preferences,
            current_request=request,
            current_occasion=occasion,
            party_size=party_size,
            time_of_day=time_of_day
        )
        
        # Show current request context
        print(f"\n🔍 Request Context:")
        print(f"Request: {request}")
        if occasion:
            print(f"Occasion: {occasion}")
        if party_size:
            print(f"Party size: {party_size}")
        if time_of_day:
            print(f"Time: {time_of_day}")
        
        # Get recommendation
        print(f"\n🤔 [Recommendation Agent] Finding the perfect restaurant for {customer_name}...")
        result = await recommendation_agent.run(
            user_prompt=request,
            deps=context
        )
        
        # For demo purposes, map the recommendation to our restaurant database
        recommended = RESTAURANTS.get(result.data.name)
        if not recommended:
            # Find the most similar restaurant in our database
            for restaurant in RESTAURANTS.values():
                if (restaurant.cuisine == result.data.cuisine and 
                    restaurant.price_range == result.data.price_range):
                    recommended = restaurant
                    break
        
        if recommended:
            print(f"\n✨ Found recommendation: {recommended.name}")
            print(f"Cuisine: {recommended.cuisine}")
            print(f"Price Range: {recommended.price_range}")
            print(f"Location: {recommended.location}")
            print(f"Specialties: {', '.join(recommended.specialties)}")
            print(f"Average Rating: {recommended.average_rating}/5")
            print(f"Wait Time: {recommended.typical_wait_time}")
            
            dietary_info = []
            if recommended.vegetarian_friendly:
                dietary_info.append("Vegetarian-friendly")
            if recommended.gluten_free_options:
                dietary_info.append("Gluten-free options")
            if dietary_info:
                print(f"Dietary Options: {', '.join(dietary_info)}")
        
        return recommended
        
    except Exception as e:
        print(f"\n❌ Error getting recommendation: {str(e)}")
        return None

async def simulate_dining_experience(
    customer_name: str,
    restaurant: Restaurant,
    rating: int,
    liked_dishes: List[str],
    disliked_dishes: List[str],
    comments: str,
    party_size: int,
    occasion: Optional[str] = None
) -> None:
    """Simulate a dining experience and update customer preferences."""
    
    try:
        # Create dining experience
        experience = DiningExperience(
            restaurant=restaurant.name,
            date=datetime.now(),
            rating=rating,
            liked_dishes=liked_dishes,
            disliked_dishes=disliked_dishes,
            comments=comments,
            party_size=party_size,
            occasion=occasion
        )
        
        # Update customer context
        customer_ctx = CUSTOMER_CONTEXTS[customer_name]
        customer_ctx.add_visit(experience, restaurant)
        
        print(f"\n✍️ Updated {customer_name}'s preferences based on experience at {restaurant.name}")
        if rating >= 4:
            print(f"Added to favorite restaurants!")
        elif rating <= 2:
            print(f"Added to disliked restaurants.")
        
    except Exception as e:
        print(f"\n❌ Error updating preferences: {str(e)}")

async def main():
    """Demonstrate context-aware restaurant recommendations."""
    
    print("\n=== Restaurant Recommendation System with Context ===\n")
    
    # Don't clean up context files this time - we want to load existing context
    
    # Scenario 1: Alice looking for lunch
    print("\n👩 Alice's New Request:")
    print("Looking for lunch after previous visits to Bella Italia")
    
    restaurant1 = await get_restaurant_recommendation(
        customer_name="Alice",
        request="Want a light lunch, something different from Italian",
        occasion="Lunch",
        party_size=2,
        time_of_day="Afternoon"
    )
    
    if restaurant1:
        # Simulate Alice's dining experience
        await simulate_dining_experience(
            customer_name="Alice",
            restaurant=restaurant1,
            rating=4,
            liked_dishes=["Green Curry", "Spring Rolls"],
            disliked_dishes=[],
            comments="Nice change from Italian, loved the vegetarian options!",
            party_size=2,
            occasion="Lunch"
        )
    
    print("\n" + "="*50)
    
    # Scenario 2: Bob trying Japanese
    print("\n👨 Bob's New Request:")
    print("Looking for Japanese after previous steakhouse experience")
    
    restaurant2 = await get_restaurant_recommendation(
        customer_name="Bob",
        request="Want to try some high-end Japanese food",
        occasion="Date night",
        party_size=2,
        time_of_day="Evening"
    )
    
    if restaurant2:
        # Simulate Bob's dining experience
        await simulate_dining_experience(
            customer_name="Bob",
            restaurant=restaurant2,
            rating=5,
            liked_dishes=["Omakase", "Fresh Sashimi"],
            disliked_dishes=[],
            comments="Amazing Japanese food, perfect for date night",
            party_size=2,
            occasion="Date night"
        )
    
    # Print context journeys showing all visits including previous ones
    print("\n=== Complete Context Journey ===")
    CUSTOMER_CONTEXTS["Alice"].print_context_journey()
    print("\n")
    CUSTOMER_CONTEXTS["Bob"].print_context_journey()
    
    print("\n" + "="*50 + "\n")
    print("Demo completed! Showed how context persists and improves over time:")
    print("1. Loaded previous dining experiences")
    print("2. Made recommendations considering past visits")
    print("3. Updated preferences with new experiences")
    print("4. Maintained complete dining history")
    print("5. Evolved cuisine preferences")
    
    # Show where context files are saved
    print("\n📁 Context files are saved in:", CONTEXT_DIR.absolute())
    print("You can find the following files:")
    for file in CONTEXT_DIR.glob("*_context.json"):
        print(f"- {file.name}")

if __name__ == "__main__":
    asyncio.run(main())
@Karthick-840
Comment
 
Leave a comment
 
Footer
© 2025 GitHub, Inc.
Footer navigation
Terms
Privacy
Security