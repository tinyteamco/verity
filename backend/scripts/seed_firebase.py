#!/usr/bin/env python3
"""
Script to seed Firebase Auth emulator with test users using Admin SDK
"""

import os

import firebase_admin
from firebase_admin import auth

# Configure for emulator
os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"


def initialize_firebase() -> None:
    """Initialize Firebase Admin SDK for emulator"""
    if not firebase_admin._apps:
        # For emulator, we need to initialize with a project ID
        firebase_admin.initialize_app(options={"projectId": "verity-local"})


def create_user_with_claims(
    email: str, password: str, uid: str, custom_claims: dict | None = None
) -> auth.UserRecord | None:
    """Create a user in Firebase Auth emulator with custom claims"""
    try:
        # Create the user
        user = auth.create_user(uid=uid, email=email, password=password, email_verified=True)
        print(f"✅ Created user: {email} (UID: {uid})")

        # Set custom claims if provided
        if custom_claims:
            auth.set_custom_user_claims(uid, custom_claims)
            print(f"   Set custom claims: {custom_claims}")

        return user
    except Exception as e:
        print(f"❌ Failed to create user {email}: {e!s}")
        return None


def main() -> None:
    print("🔥 Seeding Firebase Auth emulator with platform admin...")

    # Initialize Firebase Admin SDK
    initialize_firebase()

    # Create single super admin user (used by tests, Postman, and manual testing)
    create_user_with_claims(
        email="admin@tinyteam.co",
        password="superadmin123",
        uid="test-super-admin",
        custom_claims={"tenant": "organization", "role": "super_admin"},
    )

    print("✅ Platform seeding complete!")
    print("\n🔑 Super admin credentials:")
    print("Email:    admin@tinyteam.co")
    print("Password: superadmin123")
    print("\n🌐 Emulator UI: http://localhost:4000/auth")
    print("\nNote: Test users will be created by pytest fixtures")


if __name__ == "__main__":
    main()
