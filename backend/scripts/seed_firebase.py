#!/usr/bin/env python3
"""
Script to seed Firebase Auth with test users using Admin SDK

Supports both Firebase Auth emulator (local) and production Firebase Auth.
"""

import argparse
import os
import sys

import firebase_admin
from firebase_admin import auth


def initialize_firebase(production: bool = False) -> None:
    """Initialize Firebase Admin SDK for emulator or production"""
    if firebase_admin._apps:
        return

    if production:
        # Production mode: use application default credentials or service account
        try:
            # Try to use application default credentials (gcloud auth application-default login)
            firebase_admin.initialize_app()
            print("✅ Initialized Firebase Admin SDK with application default credentials")
        except Exception as e:
            print(f"❌ Failed to initialize Firebase Admin SDK: {e}")
            print("   Run: gcloud auth application-default login")
            sys.exit(1)
    else:
        # Emulator mode: configure for local emulator
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"
        firebase_admin.initialize_app(options={"projectId": "verity-local"})


def create_user_with_claims(
    email: str, password: str, uid: str, custom_claims: dict | None = None
) -> auth.UserRecord | None:
    """Create a user in Firebase Auth with custom claims (idempotent)"""
    try:
        # Try to get existing user first
        try:
            user = auth.get_user_by_email(email)
            print(f"INFO: User already exists: {email} (UID: {user.uid})")

            # Update custom claims if provided
            if custom_claims:
                auth.set_custom_user_claims(user.uid, custom_claims)
                print(f"   Updated custom claims: {custom_claims}")

            return user
        except auth.UserNotFoundError:
            # User doesn't exist, create it
            user = auth.create_user(uid=uid, email=email, password=password, email_verified=True)
            print(f"✅ Created user: {email} (UID: {uid})")

            # Set custom claims if provided
            if custom_claims:
                auth.set_custom_user_claims(uid, custom_claims)
                print(f"   Set custom claims: {custom_claims}")

            return user
    except Exception as e:
        print(f"❌ Failed to create/update user {email}: {e!s}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Firebase Auth with platform admin user")
    parser.add_argument(
        "--production",
        action="store_true",
        help="Seed production Firebase Auth (default: emulator)",
    )
    args = parser.parse_args()

    if args.production:
        print("🔥 Seeding production Firebase Auth with platform admin...")
    else:
        print("🔥 Seeding Firebase Auth emulator with platform admin...")

    # Initialize Firebase Admin SDK
    initialize_firebase(production=args.production)

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

    if not args.production:
        print("\n🌐 Emulator UI: http://localhost:4000/auth")
        print("\nNote: Test users will be created by pytest fixtures")


if __name__ == "__main__":
    main()
