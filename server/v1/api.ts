import { Router } from "express";
import Prisma from "@prisma/client";
import intoStream from "into-stream";
import { BlobServiceClient, StorageSharedKeyCredential, newPipeline } from "@azure/storage-blob";
import multer from "multer";

import * as dotenv from "dotenv";
dotenv.config();

const inMemoryStorage = multer.memoryStorage();
// For whatever reason the FilePond library submits the files via the "true" name
const uploadStrategy = multer({ storage: inMemoryStorage }).single("true");

const { PrismaClient } = Prisma;
const prisma = new PrismaClient();

const sharedKeyCredential = new StorageSharedKeyCredential(
	process.env.AZURE_STORAGE_NAME as string,
	process.env.AZURE_STORAGE_KEY as string);
const pipeline = newPipeline(sharedKeyCredential);
  
const blobServiceClient = new BlobServiceClient(
	`https://${process.env.AZURE_STORAGE_NAME}.blob.core.windows.net`,
	pipeline
);

const ONE_MEGABYTE = 1024 * 1024;
const uploadOptions = { bufferSize: 4 * ONE_MEGABYTE, maxBuffers: 20 };

const containerNameScores = "scores";

const apiv1 = Router();

function isLoggedIn(req: any, res: any, next: any) {
	if (req.session.user !== undefined)
		next();
	else 
		res.status(401).send({err: `Request lacks valid authentication credentials`});
} 

// Routes
apiv1.get("/", (req, res) => {
  res.send({
    message: "Hello from the API",
  });
});

apiv1.get("/test", (req,res) => {
	res.send({message: "Looks like it works!"});
});

apiv1.post("/upload", isLoggedIn, uploadStrategy, async (req: any,res) => {
	console.log("\n\n---- New File ----")
	console.log(req.file)
	const resource = await prisma.resource.create({
		data: {
			OriginalName: req.file.originalname,
			UserID: req.session.user.UserID,
			DisplayName: req.file.originalname
		}
	});
	const blobName = `${resource.id}-${req.file.originalname}`;
	const stream = intoStream(req.file.buffer);
	const containerClient = blobServiceClient.getContainerClient(containerNameScores);
	const blockBlobClient = containerClient.getBlockBlobClient(blobName);

	try {
		await blockBlobClient.uploadStream(stream,
			uploadOptions.bufferSize, uploadOptions.maxBuffers,
			{ blobHTTPHeaders: { blobContentType: req.file.mimeType } });
		res.status(201).send({ message: "File successfully uploaded" });
	} catch (err: any) {
		res.status(500).send({ message: err.message });
	}
});

apiv1.post("/scores/review", isLoggedIn, async (req: any, res) => {
	const resources = await prisma.resource.findMany({
		where: {
			UserID: req.session.user.UserID,
			Reviewed: false,
			Hidden: false
		},
		select: {
			DisplayName: true,
			MetaData: true,
			Source: true,
			id: true
		}
	});
	res.status(200).send(resources);
});

apiv1.delete("/scores/:id", isLoggedIn, async (req:any, res) => {
	const score = await prisma.resource.findFirst({
		where: {
			id: req.params.uid,
			UserID: req.session.user.UserID
		}
	});
	if (score) {
		try {
			const blobName = `${score.id}-${score.OriginalName}`;
			const containerClient = await blobServiceClient.getContainerClient(containerNameScores);
			const blockBlobClient = containerClient.getBlockBlobClient(blobName);
			const blobDeleteResponse = blockBlobClient.delete();
			console.log((await blobDeleteResponse).clientRequestId);
			await prisma.resource.delete({
				where: {
					id: score.id
				}
			});
			res.status(200).send({message: `Deleted resource: ${blobName}}`});
		} catch(err) {
			res.status(500).send({message: err});
		}
	}
	else res.status(404).send({message: `Cannot find resource or not authorized. Resource: ${req.params.uid}; user: ${req.session.user.UserID}`});
});

apiv1.get("/user", isLoggedIn, (req: any, res) => {
	let user = {
		name: req.session.user.Name,
		email: req.session.user.Email,
		photo: req.session.user.Photo
	};
	res.send(user);
})

// Catch all for unknown routes
apiv1.get("*", (req, res) => {
	res.status(404).send({err: `Unknown api route: ${req.url}`});
});

export default apiv1;