import { Router } from "express";
import Passport from "passport";
import { Strategy } from "passport-google-oauth20";
import Prisma, { user } from "@prisma/client";

const { PrismaClient } = Prisma;

const prisma = new PrismaClient();
const auth = Router();

interface User extends user {
	Photo?: string;
}

// Auth
Passport.use(new Strategy({
	clientID: process.env["GOOGLE_CLIENT_ID"] as string,
	clientSecret: process.env["GOOGLE_CLIENT_SECRET"] as string,
	callbackURL: "/oauth2/redirect/accounts.google.com",
	scope: [ "profile", "email" ],
	passReqToCallback: true
},
async function(_accessToken, _refreshToken, _object0, profile, done) {
	try {
		//console.log(profile);
		const fedUser = await prisma.federated_credential.findFirst({
			where: {
				Provider: "accounts.google.com",
				ProfileID: profile.id
			}
		});
		let user: User | null = null;
		// Get user even if a different federation provider was used in the past
		if (profile && profile.emails && profile.emails.length)
			user = await prisma.user.findFirst({
				where: {
					Email: profile.emails[0].value
				}
			});

		if (!fedUser) {
			// Create new user if the user doesn't exist 
			// This allows the same user to use different federated login methods and remain the same user
			// Email shouldn't ever be empty so it should never use the empty string, mostly just a TS thing
			if (!user)
				user = await prisma.user.create({
					data: {
						Name: profile.displayName,
						Email: (profile?.emails?.length) ? profile.emails[0]?.value : ""
					}
				});

			await prisma.federated_credential.create({
				data: {
					UserID: user.UserID,
					Provider: "accounts.google.com",
					ProfileID: profile.id
				}
			});
		}
		if (user && profile.photos && profile.photos.length)
			user.Photo = profile.photos[0]?.value;
		done(null, user as User);
	} 
	catch(err: any) {
		done(err);
	}
}));

Passport.serializeUser(function(user: any, cb) {
	process.nextTick(function() {
		cb(null, { id: user.id, username: user.username, name: user.name });
	});
});
  
Passport.deserializeUser(function(user: any, cb) {
	process.nextTick(function() {
		return cb(null, user);
	});
});

auth.get("/login/federated/accounts.google.com", Passport.authenticate("google"));
auth.get("/oauth2/redirect/accounts.google.com", Passport.authenticate("google", { failureRedirect: "/login" }), (req: any, res) => {
	req.session.user = req.user;
	res.redirect("/");
});
auth.get("/logout", function(req: any, res, next) {
	req.session.destroy();
	req.logout();
	res.redirect("/");
});

export default auth;