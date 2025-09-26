#!/usr/bin/env python3
"""
Sample Python module for testing the analyzer.
"""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    age: Optional[int] = None

class UserManager:
    """Manages user operations."""
    
    def __init__(self):
        self.users: List[User] = []
    
    def add_user(self, user: User) -> None:
        """Add a user to the manager."""
        self.users.append(user)
    
    def get_user(self, email: str) -> Optional[User]:
        """Get user by email."""
        for user in self.users:
            if user.email == email:
                return user
        return None

def create_user(name: str, email: str, age: int = None) -> User:
    """Create a new user instance."""
    return User(name=name, email=email, age=age)

def main():
    """Main function."""
    manager = UserManager()
    user = create_user("John Doe", "john@example.com", 30)
    manager.add_user(user)
    print(f"Created user: {user.name}")

if __name__ == "__main__":
    main()
