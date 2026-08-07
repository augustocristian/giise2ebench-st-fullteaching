using FullTeaching.E2E.Common;
using FullTeaching.E2E.Utils;
using NUnit.Framework;

namespace FullTeaching.E2E.Tests;

/// <summary>Ported from functional/test/UserTest.java.</summary>
[TestFixture]
public class UserTests : BaseTest
{
    /// <summary>
    /// A simple login acknowledgement: log in, confirm it worked, log out, confirm that too.
    /// Resources (RETORCH @AccessMode in the Java suite, informational only here):
    /// loginservice(READONLY,10) openvidu(NOACCESS,10) executor/webbrowser/webserver(READWRITE,1).
    /// </summary>
    [TestCaseSource(typeof(ParameterLoader), nameof(ParameterLoader.GetTestUsers))]
    public async Task LoginTest(string mail, string password, string role)
    {
        await LoginHelper.SlowLoginAsync(User, mail, password);
        await UserUtilities.CheckLoginAsync(User, mail);

        await LoginHelper.LogoutAsync(User);
        await UserUtilities.CheckLogOutAsync(User);
    }
}
