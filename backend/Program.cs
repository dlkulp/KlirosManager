using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Google;
using Microsoft.AspNetCore.Authorization;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();
builder.Services.AddAuthorization();
builder.Services.AddAuthentication(o =>
{
	// This forces challenge results to be handled by Google OpenID Handler, so there's no
	// need to add an AccountController that emits challenges for Login.
	o.DefaultChallengeScheme = GoogleDefaults.AuthenticationScheme;
	// This forces forbid results to be handled by Google OpenID Handler, which checks if
	// extra scopes are required and does automatic incremental auth.
	o.DefaultForbidScheme = GoogleDefaults.AuthenticationScheme;
	// Default scheme that will handle everything else.
	// Once a user is authenticated, the OAuth2 token info is stored as JWT.
	o.DefaultScheme = CookieAuthenticationDefaults.AuthenticationScheme;
})
.AddCookie(options => {
	options.LoginPath = "/account/google-login";
})
.AddGoogle(options =>
{
	options.ClientId = builder.Configuration.GetValue<string>("Authentication:Google:ClientID");
	options.ClientSecret = builder.Configuration.GetValue<string>("Authentication:Google:ClientSecret");
	//options.CallbackPath = "/oauth2/redirect/accounts.google.com";
	options.Scope.Add("profile");
	options.Scope.Add("email");
});

// builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
//     .AddJwtBearer(JwtBearerDefaults.AuthenticationScheme,
//         options => builder.Configuration.Bind("JwtSettings", options));

var app = builder.Build();
var conString = builder.Configuration.GetConnectionString("KlirosManagerDB") ??
		throw new InvalidOperationException("Connection string 'KlirosManagerDB'" +
		" not found.");
var db = new KlirosManagerContext(conString);

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();

// app.MapGet("/account/google-login", async (HttpRequest req) => {
// 	var properties = new AuthenticationProperties { RedirectUri = "/google-response"};
// 	await req.HttpContext.ChallengeAsync(GoogleDefaults.AuthenticationScheme, properties);
// });
// app.MapGet("/google-response", async (HttpContext req) => {
// 	var result = await req.AuthenticateAsync(CookieAuthenticationDefaults.AuthenticationScheme);
// 	if (!result.Succeeded)
// 		req.Response.Redirect("/");
// 	var claims = result.Principal.Identities.FirstOrDefault().Claims.Select(claim => new {
// 		claim.Issuer,
// 		claim.OriginalIssuer,
// 		claim.Type,
// 		claim.Value,
// 	});
// 	req.Response.Redirect("/");
// });
	// Get and save user info
	// FederatedCredential? fedCred = await req.ReadFromJsonAsync<FederatedCredential>();
	// FederatedCredential? fedUser = db.FederatedCredentials.Where(fc => 
	// 	fc.Provider == "accounts.google.com" && 
	// 	fc.ProfileID == fedCred.ProfileID
	// ).FirstOrDefault();

	// if (fedUser == null) {
	// 	//db.Users.Add(new User({UserID: fedCred.User.UserID, }))
	// }

	//req.Response.Redirect("/");
	//return;
//});

var summaries = new[]
{
    "Freezing", "Bracing", "Chilly", "Cool", "Mild", "Warm", "Balmy", "Hot", "Sweltering", "Scorching"
};

app.MapGet("/weatherforecast", () =>
{
    var forecast = Enumerable.Range(1, 5).Select(index =>
        new WeatherForecast
        (
            DateOnly.FromDateTime(DateTime.Now.AddDays(index)),
            Random.Shared.Next(-20, 55),
            summaries[Random.Shared.Next(summaries.Length)]
        ))
        .ToArray();
    return forecast;
})
.WithName("GetWeatherForecast");

app.MapGet("/api/test-ef", () => {
	return db.Metadata.OrderBy(m => m.ID);
}).RequireAuthorization();

app.MapGet("/api/test-auth", async (req) => {
	var result = await req.AuthenticateAsync(CookieAuthenticationDefaults.AuthenticationScheme);
	if (!result.Succeeded)
		req.Response.Redirect("/");
	await req.Response.WriteAsync(Newtonsoft.Json.JsonConvert.SerializeObject(result.Principal.Identities.FirstOrDefault().Claims.Select(claim => new {
		claim.Issuer,
		claim.OriginalIssuer,
		claim.Type,
		claim.Value,
	})));
	return;
}).RequireAuthorization();

app.MapGet("/signout", async (HttpContext req) => {
	await req.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
	req.Response.Redirect("/");
});

app.MapGet("/", () => {
	return "Hello World";
});

app.Run();

record WeatherForecast(DateOnly Date, int TemperatureC, string? Summary)
{
    public int TemperatureF => 32 + (int)(TemperatureC / 0.5556);
}
